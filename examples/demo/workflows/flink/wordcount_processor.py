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
from typing import List

from pyflink.table import Table, DataTypes, TableDescriptor, Schema
from pyflink.table.expressions import col, lit

from ai_flow_plugins.job_plugins import flink
from ai_flow_plugins.job_plugins.flink import ExecutionContext, UDFWrapper


# Word count job's input data
class WordCountData(object):
    word_count_data = ['flink', 'pyflink', 'flink']


class WordCountProcessor(flink.flink_processor.FlinkPythonProcessor):

    def process(self, execution_context: ExecutionContext, input_list: List[Table] = None) -> List[Table]:
        t_env = execution_context.table_env
        input_data = t_env.from_elements(map(lambda i: (i,), WordCountData.word_count_data),
                                         DataTypes.ROW([DataTypes.FIELD('line', DataTypes.STRING())]))

        t_env.create_temporary_table(
            'sink',
            TableDescriptor.for_connector('print')
                .schema(Schema.new_builder()
                        .column('word', DataTypes.STRING())
                        .column('count', DataTypes.BIGINT())
                        .build())
                .build())
        t = input_data.alias('word') \
            .group_by(col('word')) \
            .select(col('word'), lit(1).count)
        execution_context.statement_set.add_insert('sink', t)
        return []


class WordCountSqlProcessor(flink.flink_processor.FlinkSqlProcessor):

    def sql_statements(self, execution_context: ExecutionContext) -> List[str]:
        t_env = execution_context.table_env
        input_data = t_env.from_elements(map(lambda i: (i,), WordCountData.word_count_data),
                                         DataTypes.ROW([DataTypes.FIELD('word', DataTypes.STRING())]))
        t_env.create_temporary_view('source', input_data, col('word'))
        sink_ddl = """
            create table sink (
                word STRING,
                `count` BIGINT
            ) with (
                'connector' = 'print'
            )
        """
        insert_stmt = """
            INSERT INTO sink SELECT word, COUNT(word) from source GROUP BY word
        """

        return [sink_ddl, insert_stmt]

    def udf_list(self, execution_context: ExecutionContext) -> List[UDFWrapper]:
        return []