#
# Copyright 2022 The AI Flow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
import getopt
import io
import json
import logging
import os
import sys
import time
import zipfile

from ai_flow.ai_graph.ai_graph import AIGraph
from ai_flow.ai_graph.ai_node import AINode, ReadDatasetNode, WriteDatasetNode
from ai_flow.ai_graph.data_edge import DataEdge
from ai_flow.endpoint.server.server_config import AIFlowServerConfig
from ai_flow.meta.workflow_meta import WorkflowMeta
from ai_flow.plugin_interface.scheduler_interface import Scheduler, SchedulerFactory
from ai_flow.scheduler_service.service.config import SchedulerServiceConfig
from ai_flow.common.configuration.helpers import AIFLOW_HOME
from ai_flow.store.abstract_store import Filters, AbstractStore, Orders
from ai_flow.store.db.db_util import create_db_store
from ai_flow.util.json_utils import loads, Jsonable, dumps
from ai_flow.version import __version__
from ai_flow.workflow.control_edge import ControlEdge
from django.core.paginator import Paginator
from flask import Flask, request, render_template, Response, make_response, redirect
from flask_cors import CORS
from logging.config import dictConfig
from typing import List, Dict
from werkzeug.local import LocalProxy


def config_logging():
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })


app = Flask(__name__, static_folder='./dist', template_folder='./dist', static_url_path='')
CORS(app=app)

store: AbstractStore = None
scheduler: Scheduler = None
airflow: str = None
config: AIFlowServerConfig = None
logger = logging.getLogger(__name__)


def init(store_uri: str, scheduler_class: str, airflow_web_server_uri: str):
    global store
    store = create_db_store(store_uri)
    global scheduler
    scheduler = SchedulerFactory.create_scheduler(scheduler_class,
                                                  {'notification_server_uri': None, 'airflow_deploy_path': None})
    global airflow
    airflow = airflow_web_server_uri


class Edge(Jsonable):
    def __init__(self, id: str = None, name: str = None, is_signal: int = 1, is_closed_loop_node: bool = True,
                 dag_data_type: str = None):
        self._id = id
        self._name = name
        self._is_signal = is_signal
        self._is_closed_loop_node = is_closed_loop_node
        self._dag_data_type = dag_data_type

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def to_dict(self):
        return {'id': self._id, 'name': self._name, 'isSignal': self._is_signal,
                'isClosedLoopNode': self._is_closed_loop_node,
                'dagDataType': self._dag_data_type}


class Node(Jsonable):

    def __init__(self, id: str = None, layer: int = None, parent: List[Edge] = None, children: List[Edge] = None,
                 node_type: int = None, is_virtual: int = None, name: str = None, job_type_name=None,
                 is_real_node: bool = True, job_id: int = None, source_flag: bool = None, rsuuid: str = None,
                 data_name: str = None, source_type: str = None, material_id: str = None, material_ready: bool = False,
                 material_parent_project_id: int = None):
        self._id = id
        self._layer = layer
        self._parent = parent
        self._children = children
        self._node_type = node_type
        self._is_virtual = is_virtual
        self._name = name
        self._job_type_name = job_type_name
        self._is_real_node = is_real_node
        self._job_id = job_id
        self._source_flag = source_flag
        self._rsuuid = rsuuid
        self._data_name = data_name
        self._source_type = source_type
        self._material_id = material_id
        self._material_ready = material_ready
        self._material_parent_project_id = material_parent_project_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def layer(self) -> int:
        return self._layer

    @layer.setter
    def layer(self, layer: int):
        self._layer = layer

    @property
    def parent(self) -> List[Edge]:
        return self._parent

    @parent.setter
    def parent(self, parent: List[Edge]):
        self._parent = parent

    @property
    def children(self) -> List[Edge]:
        return self._children

    @children.setter
    def children(self, children: List[Edge]):
        self._children = children

    @property
    def name(self) -> str:
        return self._name

    @property
    def data_name(self) -> str:
        return self._data_name

    def to_dict(self):
        return {'id': self._id, 'layer': self._layer,
                'parent': None if self._parent is None else [edge.to_dict() for edge in self._parent],
                'children': None if self._children is None else [edge.to_dict() for edge in self._children],
                'nodeType': self._node_type, 'isVirtual': self._is_virtual, 'name': self._name,
                'jobTypeName': self._job_type_name,
                'isRealNode': self._is_real_node, 'jobId': self._job_id, 'sourceFlag': self._source_flag,
                'rsuuid': self._rsuuid, 'dataName': self._data_name,
                'sourceType': self._source_type, 'materialId': self._material_id, 'materialReady': self._material_ready,
                'materialParentProjectId': self._material_parent_project_id}


def node_layer(node: Node, parent_edges: Dict, nodes: Dict, parent_nodes: List = None):
    if node.id not in parent_edges:
        return 1
    else:
        max_layer = 1
        parent_nodes = parent_nodes if parent_nodes else [node.id]
        for parent_edge in parent_edges[node.id]:
            if parent_edge.id not in parent_nodes:
                parent_nodes.append(parent_edge.id)
                layer = 1 + node_layer(nodes[parent_edge.id], parent_edges, nodes, parent_nodes)
                if layer > max_layer:
                    max_layer = layer
        return max_layer


def generate_graph(workflow_meta: WorkflowMeta):
    workflow_graph: AIGraph = extract_graph(workflow_meta)
    workflow_nodes, id_nodes, name_nodes = build_nodes(workflow_graph)
    parent_edges, children_edges = build_edges(workflow_graph, workflow_nodes, id_nodes, name_nodes)
    return build_graph(name_nodes, parent_edges, children_edges)


def extract_graph(workflow_meta: WorkflowMeta):
    graph_meta: Dict[str, str] = json.loads(workflow_meta.graph, strict=False)
    if '_context_extractor' in graph_meta:
        graph_meta.pop('_context_extractor', None)
    return loads(dumps(graph_meta))


def build_nodes(workflow_graph: AIGraph):
    workflow_nodes: Dict[str, AINode] = {}
    id_nodes: Dict[str, Node] = {}
    name_nodes: Dict[str, Node] = {}
    for graph_node in workflow_graph.nodes.values():
        workflow_nodes.update({graph_node.node_id: graph_node})
        if isinstance(graph_node, ReadDatasetNode) or isinstance(graph_node, WriteDatasetNode):
            data_node = Node(id=graph_node.dataset().name, source_flag=True,
                             data_name=graph_node.dataset().name)
            id_nodes.update({graph_node.node_id: data_node})
            name_nodes.update({graph_node.dataset().name: data_node})
        else:
            job_node = Node(id=graph_node.config.job_name, node_type=0, name=graph_node.config.job_name,
                            job_type_name=graph_node.config.job_type, source_flag=False)
            id_nodes.update({graph_node.node_id: job_node})
            name_nodes.update({graph_node.config.job_name: job_node})
    return workflow_nodes, id_nodes, name_nodes


def build_edges(workflow_graph: AIGraph, workflow_nodes: Dict[str, AINode], id_nodes: Dict[str, Node],
                name_nodes: Dict[str, Node]):
    parent_edges: Dict[str, List[Edge]] = {}
    children_edges: Dict[str, List[Edge]] = {}
    for graph_edges in workflow_graph.edges.values():
        for graph_edge in graph_edges:
            if isinstance(graph_edge, DataEdge):
                source_workflow_node: AINode = workflow_nodes.get(graph_edge.source)
                destination_workflow_node: AINode = workflow_nodes.get(graph_edge.destination)
                dag_data_type = 'source' if isinstance(source_workflow_node, ReadDatasetNode) else 'sink'
                source_node: Node = id_nodes.get(graph_edge.source)
                source_name = source_node.data_name \
                    if isinstance(source_workflow_node, ReadDatasetNode) \
                    else source_node.name
                source_edge: Edge = Edge(id=source_name, name=source_name, dag_data_type=dag_data_type, )
                destination_node: Node = id_nodes.get(graph_edge.destination)
                destination_name = destination_node.data_name \
                    if isinstance(destination_workflow_node, WriteDatasetNode) \
                    else destination_node.name
                destination_edge: Edge = Edge(id=destination_name, name=destination_name,
                                              dag_data_type=dag_data_type)
                if source_name != destination_name:
                    if source_name in children_edges:
                        children_edges[source_name].append(destination_edge)
                    else:
                        children_edges[source_name] = [destination_edge]
                    if destination_name in parent_edges:
                        parent_edges[destination_name].append(source_edge)
                    else:
                        parent_edges[destination_name] = [source_edge]
            else:
                control_edge: ControlEdge = graph_edge
                for event in control_edge.scheduling_rule.event_condition.events:
                    if event.sender != '*':
                        sender_event_edge: Edge = Edge(id=name_nodes[event.sender].id,
                                                       name=name_nodes[event.sender].name,
                                                       dag_data_type='event')
                        receiver_event_edge: Edge = Edge(id=name_nodes[control_edge.destination].id,
                                                         name=name_nodes[control_edge.destination].name,
                                                         dag_data_type='event')
                        if name_nodes[event.sender].id in children_edges:
                            children_edges[name_nodes[event.sender].id].append(receiver_event_edge)
                        else:
                            children_edges[name_nodes[event.sender].id] = [receiver_event_edge]
                        if name_nodes[control_edge.destination].id in parent_edges:
                            parent_edges[name_nodes[control_edge.destination].id].append(sender_event_edge)
                        else:
                            parent_edges[name_nodes[control_edge.destination].id] = [sender_event_edge]
    return parent_edges, children_edges


def build_graph(name_nodes: Dict[str, Node], parent_edges: Dict[str, List[Edge]],
                children_edges: Dict[str, List[Edge]]):
    node_layers = {}
    for name_node in name_nodes.values():
        name_node.layer = node_layer(name_node, parent_edges, name_nodes)
        if name_node.id in parent_edges:
            name_node.parent = parent_edges[name_node.id]
        if name_node.id in children_edges:
            name_node.children = children_edges[name_node.id]
        node_layers.update({name_node.id: name_node})
    graph_nodes = []
    for graph_node in node_layers.values():
        if graph_node.parent:
            for parent_node in graph_node.parent:
                node_layers[parent_node.id].layer = graph_node.layer - 1
        graph_nodes.append(graph_node.to_dict())
    return json.dumps(graph_nodes)


def store_inner_class(inner_name: str):
    return getattr(sys.modules[store.__module__], inner_name)


def build_filters(req: LocalProxy):
    filters = Filters()
    for key, value in req.args.items():
        if key not in ('pageNo', 'pageSize', 'sortField', 'sortOrder') and value:
            filters.add_filter((store_inner_class('FilterEqual')(key), value))
    return filters


def build_orders(req: LocalProxy):
    orders = Orders()
    if 'sortField' in req.args.keys() and 'sortOrder' in req.args.keys():
        orders.add_order((store_inner_class('OrderBy')(req.args['sortField']), req.args['sortOrder']))
    return orders


def pagination_response(page_no: int, total_count: int, data: List):
    return dumps({'pageNo': page_no, 'totalCount': total_count, 'data': data})


def json_pagination_response(page_no: int, total_count: int, data: List):
    return json.dumps({'pageNo': page_no, 'totalCount': total_count, 'data': data})


def make_zip(source_dir, target_file):
    if os.path.exists(target_file):
        os.remove(target_file)
    zip_file = zipfile.ZipFile(os.path.join(source_dir, target_file), 'w')
    for parent, dirs, files in os.walk(source_dir):
        for file in files:
            if file != target_file:
                file_path = os.path.join(parent, file)
                zip_file.write(file_path, file_path[len(os.path.dirname(source_dir)):].strip(os.path.sep))
    zip_file.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/metadata/<meta>')
def metadata(meta):
    return render_template('index.html')


@app.route('/graph/<project_id>/<workflow_name>')
def graph(project_id, workflow_name):
    return render_template('index.html')


@app.route('/version')
def version():
    return __version__


@app.route('/project')
def project_metadata():
    project_count = store.count_projects(filters=build_filters(request))
    project_list = store.list_projects(page_size=int(request.args.get('pageSize')),
                                       offset=(int(request.args.get('pageNo')) - 1) * int(request.args.get('pageSize')),
                                       filters=build_filters(request), orders=build_orders(request))
    return pagination_response(page_no=int(request.args.get('pageNo')), total_count=project_count,
                               data=project_list if project_list else [])


@app.route('/workflow')
def workflow_metadata():
    workflow_count = store.count_workflows(filters=build_filters(request))
    workflow_list = store.list_workflows(page_size=int(request.args.get('pageSize')),
                                         offset=(int(request.args.get('pageNo')) - 1) * int(
                                             request.args.get('pageSize')),
                                         filters=build_filters(request), orders=build_orders(request))
    return pagination_response(page_no=int(request.args.get('pageNo')), total_count=workflow_count,
                               data=workflow_list if workflow_list else [])


@app.route('/workflow/data-view')
def data_view():
    project_id = request.args.get('project_id')
    workflow_name = request.args.get('workflow_name')
    project_meta = store.get_project_by_id(project_id)
    if project_meta is None:
        raise Exception('The project({}) for the workflow({}) is not found.'.format(project_id, workflow_name))
    workflow_meta = store.get_workflow_by_name(project_name=project_meta.name, workflow_name=workflow_name)
    if workflow_meta is None:
        raise Exception('The workflow({}) of the project({}) is not found.'.format(workflow_name, project_id))
    else:
        return generate_graph(workflow_meta)


@app.route('/workflow/task-view')
def task_view():
    project_id = request.args.get('project_id')
    workflow_name = request.args.get('workflow_name')
    project_meta = store.get_project_by_id(project_id)
    if project_meta is None:
        raise Exception('The project({}) for the workflow({}) is not found.'.format(project_id, workflow_name))
    workflow_meta = store.get_workflow_by_name(project_name=project_meta.name, workflow_name=workflow_name)
    if workflow_meta is None:
        raise Exception('The workflow({}) of the project({}) is not found.'.format(workflow_name, project_id))
    else:
        return '{}/graph?dag_id={}'.format(airflow, '{}.{}'.format(project_meta.name, workflow_name))


@app.route('/workflow-execution')
def workflow_execution_metadata():
    project_name = request.args.get('project_name')
    workflow_name = request.args.get('workflow_name')
    workflow_execution_list = scheduler.list_workflow_executions(project_name,
                                                                 workflow_name) if project_name and workflow_name else None
    return pagination_response(page_no=int(request.args.get('pageNo')),
                               total_count=len(workflow_execution_list) if workflow_execution_list else 0,
                               data=Paginator(workflow_execution_list, int(request.args.get('pageSize'))).get_page(
                                   int(request.args.get('pageNo'))).object_list if workflow_execution_list else [])


@app.route('/job-execution')
def job_execution_metadata():
    workflow_execution_id = request.args.get('workflow_execution_id')
    job_execution_list = scheduler.list_job_executions(workflow_execution_id) if workflow_execution_id else None
    page_job_executions = Paginator(job_execution_list, int(request.args.get('pageSize'))).get_page(
      int(request.args.get('pageNo'))).object_list if job_execution_list else None
    job_execution_objects = []
    if page_job_executions:
        workflow_info = page_job_executions[0].workflow_execution.workflow_info
        workflow_graph = extract_graph(store.get_workflow_by_name(workflow_info.namespace,
                                                                  workflow_info.workflow_name))
        job_types = {}
        for node in workflow_graph.nodes.values():
            job_types.update({node.config.job_name: node.config.job_type})
        for page_job_execution in page_job_executions:
            job_execution_object = page_job_execution.__dict__
            job_execution_object.update({'_job_type': job_types.get(page_job_execution.job_name)})
            job_execution_objects.append(job_execution_object)
    return pagination_response(page_no=int(request.args.get('pageNo')),
                                total_count=len(job_execution_list) if job_execution_list else 0,
                                data=job_execution_objects)


@app.route('/job-execution/log')
def job_execution_log():
    job_type = request.args.get('job_type')
    job_execution_id = request.args.get('job_execution_id')
    workflow_execution_id = request.args.get('workflow_execution_id')
    job_executions = scheduler.get_job_executions(request.args.get('job_name'),
                                                  workflow_execution_id)
    log_job_execution = None
    for job_execution in job_executions:
        if job_execution.job_execution_id == job_execution_id:
            log_job_execution = job_execution
            break
    if log_job_execution:
        if job_type == 'bash':
            return redirect('{}/graph?dag_id={}'.format(airflow, workflow_execution_id.split('|')[0]))
        else:
            base_log_folder = config.get_base_log_folder()
            log_dir = os.path.join(base_log_folder if base_log_folder else AIFLOW_HOME, 'logs',
                                   log_job_execution.workflow_execution.workflow_info.namespace,
                                   log_job_execution.workflow_execution.workflow_info.workflow_name,
                                   log_job_execution.job_name,
                                   log_job_execution.job_execution_id)
            if os.path.exists(log_dir):
                log_file = 'logs.zip'
                make_zip(log_dir, log_file)
                file_obj = io.BytesIO()
                with zipfile.ZipFile(file_obj, 'w') as zip_file:
                    zip_info = zipfile.ZipInfo(log_file)
                    zip_info.date_time = time.localtime(time.time())[:6]
                    zip_info.compress_type = zipfile.ZIP_DEFLATED
                    with open(os.path.join(log_dir, log_file), 'rb') as fd:
                        zip_file.writestr(zip_info, fd.read())
                file_obj.seek(0)
                return Response(file_obj.getvalue(),
                                mimetype='application/zip',
                                headers={'Content-Disposition': 'attachment;filename={}'.format(log_file)})
    return make_response('No log found.')


@app.route('/dataset')
def dataset_metadata():
    dataset_count = store.count_datasets(filters=build_filters(request))
    dataset_list = store.list_datasets(page_size=int(request.args.get('pageSize')),
                                       offset=(int(request.args.get('pageNo')) - 1) * int(request.args.get('pageSize')),
                                       filters=build_filters(request), orders=build_orders(request))
    return pagination_response(page_no=int(request.args.get('pageNo')), total_count=dataset_count,
                               data=dataset_list if dataset_list else [])


@app.route('/model')
def model_metadata():
    model_count = store.count_registered_models(filters=build_filters(request))
    model_list = store.list_registered_models(page_size=int(request.args.get('pageSize')),
                                              offset=(int(request.args.get('pageNo')) - 1) * int(
                                                  request.args.get('pageSize')),
                                              filters=build_filters(request), orders=build_orders(request))
    return json_pagination_response(page_no=int(request.args.get('pageNo')), total_count=model_count,
                                    data=[{'model_name': model.model_name, 'model_desc': model.model_desc} for model in
                                          model_list] if model_list else [])


@app.route('/model-version')
def model_version_metadata():
    model_version_count = store.count_model_versions(filters=build_filters(request))
    model_version_list = store.list_model_versions(page_size=int(request.args.get('pageSize')),
                                                   offset=(int(request.args.get('pageNo')) - 1) * int(
                                                       request.args.get('pageSize')),
                                                   filters=build_filters(request), orders=build_orders(request))
    return json_pagination_response(page_no=int(request.args.get('pageNo')), total_count=model_version_count,
                                    data=[model_version.__dict__ for model_version in
                                          model_version_list] if model_version_list else [])


@app.route('/artifact')
def artifact_metadata():
    artifact_count = store.count_artifacts(filters=build_filters(request))
    artifact_list = store.list_artifacts(page_size=int(request.args.get('pageSize')),
                                         offset=(int(request.args.get('pageNo')) - 1) * int(
                                             request.args.get('pageSize')),
                                         filters=build_filters(request), orders=build_orders(request))
    return pagination_response(page_no=int(request.args.get('pageNo')), total_count=artifact_count,
                               data=artifact_list if artifact_list else [])


usage_message = """
usage: web_server.py -c <config_path>
"""


class AIFlowWebServerConfig:

    def __init__(self, config: Dict):
        self.config = config

    def host(self):
        return self.config['host']

    def port(self):
        return self.config['port']

    def get(self, key):
        return self.config.get(key)

    def __repr__(self):
        return self.config.__repr__()

    def __eq__(self, other):
        return self.config.__eq__(other.config)


def main(argv):
    config_logging()
    config_file = None
    try:
        opts, args = getopt.getopt(argv, "hc:",
                                   ["config="])
    except getopt.GetoptError:
        print(usage_message)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usage_message)
            sys.exit()
        elif opt in ("-c", "--config"):
            config_file = arg

    if config_file is None:
        print(usage_message)
        sys.exit(2)

    start_web_server_by_config_file_path(config_file)


def start_web_server_by_config_file_path(config_file_path):
    global config
    config = AIFlowServerConfig()
    config.load_from_file(config_file_path)
    store_uri = config.get_db_uri()
    scheduler_service_config = SchedulerServiceConfig(config.get_scheduler_service_config())
    scheduler_class = scheduler_service_config.scheduler().scheduler_class()
    web_server_config = AIFlowWebServerConfig(config.get_web_server_config())

    start_web_server(scheduler_class, store_uri, web_server_config)


def start_web_server(scheduler_class, store_uri, web_server_config):
    logger.info("Starting web server with scheduler class: {}, store_uri: {}, web_server_config: {}"
                .format(scheduler_class, store_uri, web_server_config))
    init(store_uri, scheduler_class, web_server_config.get('airflow_web_server_uri'))
    app.run(host=web_server_config.host(), port=int(web_server_config.port()))


if __name__ == '__main__':
    main(sys.argv[1:])
