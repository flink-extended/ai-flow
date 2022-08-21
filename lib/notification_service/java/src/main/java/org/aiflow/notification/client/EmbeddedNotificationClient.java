/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
package org.aiflow.notification.client;

import com.google.common.util.concurrent.ThreadFactoryBuilder;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import org.aiflow.notification.entity.EventKey;
import org.aiflow.notification.entity.EventMeta;
import org.aiflow.notification.entity.SenderEventCount;
import org.aiflow.notification.proto.NotificationServiceGrpc;
import org.aiflow.notification.proto.NotificationServiceOuterClass;
import org.aiflow.notification.conf.Configuration;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.tuple.ImmutablePair;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.aiflow.notification.conf.Configuration.CLIENT_ENABLE_IDEMPOTENCE_CONFIG_DEFAULT_VALUE;
import static org.aiflow.notification.conf.Configuration.CLIENT_ENABLE_IDEMPOTENCE_CONFIG_KEY;
import static org.aiflow.notification.conf.Configuration.CLIENT_ID_CONFIG_DEFAULT_VALUE;
import static org.aiflow.notification.conf.Configuration.CLIENT_ID_CONFIG_KEY;
import static org.aiflow.notification.conf.Configuration.CLIENT_INITIAL_SEQUENCE_NUMBER_CONFIG_DEFAULT_VALUE;
import static org.aiflow.notification.conf.Configuration.CLIENT_INITIAL_SEQUENCE_NUMBER_CONFIG_KEY;
import static org.aiflow.notification.conf.Configuration.HA_CLIENT_LIST_MEMBERS_INTERVAL_MS_CONFIG_DEFAULT_VALUE;
import static org.aiflow.notification.conf.Configuration.HA_CLIENT_LIST_MEMBERS_INTERVAL_MS_CONFIG_KEY;
import static org.aiflow.notification.conf.Configuration.HA_CLIENT_RETRY_INTERVAL_MS_CONFIG_DEFAULT_VALUE;
import static org.aiflow.notification.conf.Configuration.HA_CLIENT_RETRY_INTERVAL_MS_CONFIG_KEY;
import static org.aiflow.notification.conf.Configuration.HA_CLIENT_RETRY_TIMEOUT_MS_CONFIG_DEFAULT_VALUE;
import static org.aiflow.notification.conf.Configuration.HA_CLIENT_RETRY_TIMEOUT_MS_CONFIG_KEY;

public class EmbeddedNotificationClient extends NotificationClient{

    private static final Logger logger = LoggerFactory.getLogger(EmbeddedNotificationClient.class);
    public static String ANY_CONDITION = "*";
    private static final String SERVER_URI = "localhost:50051";
    private final String defaultNamespace;
    private final Map<String, EventListener> threads;
    private final ExecutorService listMembersService;
    private ManagedChannel channel;
    private NotificationServiceGrpc.NotificationServiceBlockingStub notificationServiceStub;
    private Set<NotificationServiceOuterClass.MemberProto> livingMembers;
    private Boolean enableHa;
    private String currentUri;
    private String sender;
    private Long clientId;
    private AtomicInteger sequenceNum;
    private final Configuration conf;

    public EmbeddedNotificationClient(
            String target,
            String defaultNamespace,
            String sender,
            Properties properties)
            throws Exception {
        this.defaultNamespace = defaultNamespace;
        this.sender = sender;
        this.conf = new Configuration(properties);

        String[] serverUris = StringUtils.split(target, ",");
        if (serverUris.length > 1) {
            this.enableHa = true;
            boolean lastError = true;
            for (String serverUri : serverUris) {
                currentUri = serverUri;
                try {
                    initNotificationServiceStub();
                    lastError = false;
                    break;
                } catch (Exception e) {
                    continue;
                }
            }
            if (lastError) {
                logger.warn("Failed to initialize client");
            }
        } else {
            this.enableHa = false;
            this.currentUri = target;
            initNotificationServiceStub();
        }

        long clientId = this.conf.getLong(CLIENT_ID_CONFIG_KEY, CLIENT_ID_CONFIG_DEFAULT_VALUE);
        int initialSeqNum =
                this.conf.getInt(
                        CLIENT_INITIAL_SEQUENCE_NUMBER_CONFIG_KEY,
                        CLIENT_INITIAL_SEQUENCE_NUMBER_CONFIG_DEFAULT_VALUE);
        if (clientId < 0) {
            this.clientId = registerClient();
        } else {
            if (checkClientExists(clientId)) {
                this.clientId = clientId;
            } else {
                throw new Exception(
                        "Init notification client with a client id which have not registered.");
            }
        }
        this.sequenceNum = new AtomicInteger(initialSeqNum);

        threads = new HashMap<>();
        livingMembers = new HashSet<>();
        listMembersService =
                Executors.newSingleThreadExecutor(
                        new ThreadFactoryBuilder()
                                .setDaemon(true)
                                .setNameFormat("list-members-%d")
                                .build());
        listMembersService.submit(listMembers());
    }

    /**
     * *
     *
     * @return Id of registered client
     */
    private long registerClient() throws Exception {
        NotificationServiceOuterClass.RegisterClientRequest registerClientRequest =
                NotificationServiceOuterClass.RegisterClientRequest.newBuilder()
                        .setClientMeta(
                                NotificationServiceOuterClass.ClientMeta.newBuilder()
                                        .setNamespace(defaultNamespace)
                                        .setSender(sender)
                                        .build())
                        .build();
        NotificationServiceOuterClass.RegisterClientResponse registerClientResponse =
                notificationServiceStub.registerClient(registerClientRequest);
        if (registerClientResponse.getReturnCode()
                == NotificationServiceOuterClass.ReturnStatus.SUCCESS) {
            return registerClientResponse.getClientId();
        } else {
            throw new Exception(registerClientResponse.getReturnMsg());
        }
    }

    private boolean checkClientExists(long clientId) {
        NotificationServiceOuterClass.ClientIdRequest request =
                NotificationServiceOuterClass.ClientIdRequest.newBuilder()
                        .setClientId(clientId)
                        .build();
        NotificationServiceOuterClass.isClientExistsResponse response =
                notificationServiceStub.isClientExists(request);
        if (response.getReturnCode() == NotificationServiceOuterClass.ReturnStatus.SUCCESS
                && response.getIsExists()) {
            return true;
        } else {
            return false;
        }
    }

    /**
     * List specific registered listener events in Notification Service.
     *
     * @param serviceStub Notification service GRPC stub.
     * @param event_name Name of events to be listed, null indicates not filter by name.
     * @param namespace Namespace of events to be listed, null indicates not filter by namespace.
     * @param eventType Type of events to be listed, null indicates not filter by type.
     * @param sender Sender of events to be listed, null indicates not filter by sender.
     * @param startOffset (Optional) The offset of events to start listing.
     * @param timeoutSeconds List events request timeout seconds.
     * @return List of event updated in Notification Service.
     */
    protected static List<EventMeta> listEvents(
            NotificationServiceGrpc.NotificationServiceBlockingStub serviceStub,
            String event_name,
            String namespace,
            String eventType,
            String sender,
            long startOffset,
            Integer timeoutSeconds)
            throws Exception {
        NotificationServiceOuterClass.ListEventsRequest request =
                NotificationServiceOuterClass.ListEventsRequest.newBuilder()
                        .addNames(event_name)
                        .setNamespace(namespace)
                        .setEventType(eventType)
                        .setSender(sender)
                        .setStartOffset(startOffset)
                        .setTimeoutSeconds(timeoutSeconds)
                        .build();
        return parseEventsFromResponse(serviceStub.listEvents(request));
    }

    protected static List<EventMeta> listAllEvents(
            NotificationServiceGrpc.NotificationServiceBlockingStub serviceStub,
            Long startTime,
            Long startOffset,
            Long endOffset,
            int timeoutSeconds)
            throws Exception {
        NotificationServiceOuterClass.ListAllEventsRequest request =
                NotificationServiceOuterClass.ListAllEventsRequest.newBuilder()
                        .setStartTime(startTime)
                        .setStartOffset(startOffset)
                        .setEndOffset(endOffset)
                        .setTimeoutSeconds(timeoutSeconds)
                        .build();
        NotificationServiceOuterClass.ListEventsResponse response =
                serviceStub.listAllEvents(request);
        return parseEventsFromResponse(response);

    }

    private static List<EventMeta> parseEventsFromResponse(
            NotificationServiceOuterClass.ListEventsResponse response) throws Exception {
        if (response.getReturnCode() == NotificationServiceOuterClass.ReturnStatus.SUCCESS) {
            List<EventMeta> eventMetas = new ArrayList<>();
            for (NotificationServiceOuterClass.EventProto eventProto : response.getEventsList()) {
                eventMetas.add(EventMeta.buildEventMeta(eventProto));
            }
            return eventMetas;
        } else {
            throw new Exception(response.getReturnMsg());
        }
    }

    private static ImmutablePair<Long, List<SenderEventCount>> parseEventCountFromResponse(
            NotificationServiceOuterClass.CountEventsResponse response) throws Exception {
        if (response.getReturnCode() == NotificationServiceOuterClass.ReturnStatus.SUCCESS) {
            List<SenderEventCount> senderEventCounts = new ArrayList<>();
            for (NotificationServiceOuterClass.SenderEventCountProto eventCountProto :
                    response.getSenderEventCountsList()) {
                senderEventCounts.add(SenderEventCount.buildSenderEventCount(eventCountProto));
            }
            return new ImmutablePair<>(response.getEventCount(), senderEventCounts);
        } else {
            throw new Exception(response.getReturnMsg());
        }
    }

    protected static NotificationServiceGrpc.NotificationServiceBlockingStub wrapBlockingStub(
            NotificationServiceGrpc.NotificationServiceBlockingStub stub,
            String target,
            Set<NotificationServiceOuterClass.MemberProto> livingMembers,
            Boolean haRunning,
            Integer retryIntervalMs,
            Integer retryTimeoutMs) {
        return NotificationServiceGrpc.newBlockingStub(
                        ManagedChannelBuilder.forTarget(target).usePlaintext().build())
                .withInterceptors(
                        new NotificationInterceptor(
                                stub,
                                target,
                                livingMembers,
                                haRunning,
                                retryIntervalMs,
                                retryTimeoutMs));
    }

    /** Select a valid server from server candidates as current server. */
    protected void selectValidServer() {
        boolean lastError = false;
        int listMemberIntervalMs = this.conf.getInt(
                HA_CLIENT_LIST_MEMBERS_INTERVAL_MS_CONFIG_KEY,
                HA_CLIENT_LIST_MEMBERS_INTERVAL_MS_CONFIG_DEFAULT_VALUE);
        for (NotificationServiceOuterClass.MemberProto livingMember : livingMembers) {
            try {
                currentUri = livingMember.getServerUri();
                initNotificationServiceStub();
                NotificationServiceOuterClass.ListMembersRequest request =
                        NotificationServiceOuterClass.ListMembersRequest.newBuilder()
                                .setTimeoutSeconds(listMemberIntervalMs / 1000)
                                .build();
                NotificationServiceOuterClass.ListMembersResponse response =
                        notificationServiceStub.listMembers(request);
                if (response.getReturnCode()
                        == NotificationServiceOuterClass.ReturnStatus.SUCCESS) {
                    livingMembers = new HashSet<>(response.getMembersList());
                    lastError = false;
                    break;
                } else {
                    lastError = true;
                }
            } catch (Exception e) {
                lastError = true;
            }
        }
        if (lastError) {
            logger.warn("No available server uri!");
        }
    }

    /** Initialize notification service stub. */
    protected void initNotificationServiceStub() {
        if (notificationServiceStub == null) {
            channel = ManagedChannelBuilder.forTarget(
                    StringUtils.isEmpty(currentUri)
                            ? SERVER_URI
                            : currentUri)
                    .usePlaintext()
                    .build();
            notificationServiceStub =
                    NotificationServiceGrpc.newBlockingStub(channel);
        }
        if (enableHa) {
            int retryIntervalMs = this.conf.getInt(
                    HA_CLIENT_RETRY_INTERVAL_MS_CONFIG_KEY,
                    HA_CLIENT_RETRY_INTERVAL_MS_CONFIG_DEFAULT_VALUE);
            int retryTimeoutMs = this.conf.getInt(
                    HA_CLIENT_RETRY_TIMEOUT_MS_CONFIG_KEY,
                    HA_CLIENT_RETRY_TIMEOUT_MS_CONFIG_DEFAULT_VALUE);
            notificationServiceStub =
                    wrapBlockingStub(
                            notificationServiceStub,
                            StringUtils.isEmpty(currentUri) ? SERVER_URI : currentUri,
                            livingMembers,
                            enableHa,
                            retryIntervalMs,
                            retryTimeoutMs);
        }
    }

    /** List living members under high available mode. */
    protected Runnable listMembers() {
        return () -> {
            int listMemberIntervalMs = this.conf.getInt(
                    HA_CLIENT_LIST_MEMBERS_INTERVAL_MS_CONFIG_KEY,
                    HA_CLIENT_LIST_MEMBERS_INTERVAL_MS_CONFIG_DEFAULT_VALUE);
            while (enableHa) {
                try {
                    if (Thread.currentThread().isInterrupted()) {
                        break;
                    }
                    NotificationServiceOuterClass.ListMembersRequest request =
                            NotificationServiceOuterClass.ListMembersRequest.newBuilder()
                                    .setTimeoutSeconds(listMemberIntervalMs / 1000)
                                    .build();
                    NotificationServiceOuterClass.ListMembersResponse response =
                            notificationServiceStub.listMembers(request);
                    if (response.getReturnCode()
                            == NotificationServiceOuterClass.ReturnStatus.SUCCESS) {
                        livingMembers = new HashSet<>(response.getMembersList());
                    } else {
                        logger.warn(response.getReturnMsg());
                        selectValidServer();
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                    logger.warn("Error while listening notification");
                    selectValidServer();
                }
            }
        };
    }

    /** Disable high availability mode. */
    public void disableHighAvailability() {
        enableHa = false;
        listMembersService.shutdownNow();
    }

    public EventMeta sendEvent(EventMeta event)
            throws Exception {
        boolean enableIdempotence =
                this.conf.getBoolean(
                        CLIENT_ENABLE_IDEMPOTENCE_CONFIG_KEY,
                        CLIENT_ENABLE_IDEMPOTENCE_CONFIG_DEFAULT_VALUE);
        String signature = UUID.randomUUID().toString();
        if (enableIdempotence) {
            int currentSeqNum = this.sequenceNum.get();
            signature =
                    StringUtils.join(Arrays.asList("client", this.clientId, currentSeqNum), "_");
        }
        NotificationServiceOuterClass.SendEventRequest request =
                NotificationServiceOuterClass.SendEventRequest.newBuilder()
                        .setEvent(
                                NotificationServiceOuterClass.EventProto.newBuilder()
                                        .setName(event.getEventKey().getName())
                                        .setEventType(event.getEventKey().getEventType())
                                        .setNamespace(event.getEventKey().getNamespace())
                                        .setSender(event.getEventKey().getSender())
                                        .setMessage(event.getMessage())
                                        .setContext(event.getContext())
                                        .build())
                        .setUuid(signature)
                        .setEnableIdempotence(enableIdempotence)
                        .build();
        NotificationServiceOuterClass.SendEventsResponse response =
                notificationServiceStub.sendEvent(request);
        if (response.getReturnCode() == NotificationServiceOuterClass.ReturnStatus.SUCCESS) {
            if (enableIdempotence) {
                this.sequenceNum.getAndIncrement();
            }
            return EventMeta.buildEventMeta(response.getEvent());
        } else {
            throw new Exception(response.getReturnMsg());
        }
    }

    public List<EventMeta> listEvents(
            String event_name,
            String namespace,
            String eventType,
            String sender,
            Long offset) throws Exception {

        String realEventName = StringUtils.isEmpty(event_name) ? ANY_CONDITION : event_name;
        String realNamespace = StringUtils.isEmpty(namespace) ? ANY_CONDITION : namespace;
        String realEventType = StringUtils.isEmpty(eventType) ? ANY_CONDITION : eventType;
        String realSender = StringUtils.isEmpty(sender) ? ANY_CONDITION : sender;
        long realOffset = offset == null ? 0 : offset;

        return listEvents(
                notificationServiceStub,
                realEventName,
                realNamespace,
                realEventType,
                realSender,
                realOffset,
                0);
    }

    @Override
    public Long timeToOffset(Long timestamp) throws Exception {
        NotificationServiceOuterClass.TimeToOffsetRequest request =
                NotificationServiceOuterClass.TimeToOffsetRequest.newBuilder()
                .setTimestamp(timestamp)
                .build();
        NotificationServiceOuterClass.TimeToOffsetResponse response =
                notificationServiceStub.timestampToEventOffset(request);
        if (response.getReturnCode() != NotificationServiceOuterClass.ReturnStatus.SUCCESS) {
            throw new Exception("There is no event whose create_time is greater than or equal to " + timestamp);
        } else {
            return response.getOffset();
        }
    }

    /**
     * Count events in Notification Service.
     *
     * @param event_name Name of events to be listed, null indicates not filter by name.
     * @param namespace Namespace of events to be listed, null indicates not filter by namespace.
     * @param eventType Type of events to be listed, null indicates not filter by type.
     * @param sender Sender of events to be listed, null indicates not filter by sender.
     * @param offset (Optional) The offset of events to start listing.
     * @return Count of events in Notification Service.
     */
    public ImmutablePair<Long, List<SenderEventCount>> countEvents(
            String event_name,
            String namespace,
            String eventType,
            String sender,
            Long offset) throws Exception {

        String realEventName = StringUtils.isEmpty(event_name) ? ANY_CONDITION : event_name;
        String realNamespace = StringUtils.isEmpty(namespace) ? ANY_CONDITION : namespace;
        String realEventType = StringUtils.isEmpty(eventType) ? ANY_CONDITION : eventType;
        String realSender = StringUtils.isEmpty(sender) ? ANY_CONDITION : sender;
        long realOffset = offset == null ? 0 : offset;

        NotificationServiceOuterClass.CountEventsRequest request =
                NotificationServiceOuterClass.CountEventsRequest.newBuilder()
                        .addNames(realEventName)
                        .setNamespace(realNamespace)
                        .setEventType(realEventType)
                        .setSender(realSender)
                        .setStartOffset(realOffset)
                        .build();
        return parseEventCountFromResponse(notificationServiceStub.countEvents(request));
    }

    /**
     * List all registered listener events in Notification Service.
     *
     * @param startTime (Optional) The event create time after the given startTime.
     * @param startOffset (Optional) Start offset of event for listing.
     * @param endOffset (Optional) End offset of event for listing.
     * @return List of event updated in Notification Service.
     */
    public List<EventMeta> listAllEvents(Long startTime, Long startOffset, Long endOffset)
            throws Exception {
        return listAllEvents(notificationServiceStub, startTime, startOffset, endOffset, 0);
    }

    public ListenerRegistrationId registerListener(
            ListenerProcessor listenerProcessor,
            List<EventKey> eventKeys,
            Long offset) {
        String listenKey = eventKeys.toString() + offset + listenerProcessor.toString();
        EventListener listener =
                new EventListener(
                        notificationServiceStub,
                        eventKeys,
                        offset,
                        0l,
                        listenerProcessor,
                        10);
        listener.start();
        threads.put(listenKey, listener);
        return new ListenerRegistrationId(listenKey);
    }

    public void unRegisterListener(ListenerRegistrationId id) {
        String listenKey = id.getId();
        if (threads.containsKey(listenKey)) {
            threads.get(listenKey).shutdown();
            threads.remove(listenKey);
        }
    }

    /**
     * Get latest offset of specific `key` notifications in Notification Service.
     *
     * @param namespace Namespace of the event.
     * @param event_name Name of the event.
     */
    public long getLatestOffset(String namespace, String event_name) throws Exception {
        if (StringUtils.isEmpty(event_name)) {
            throw new Exception("Empty event name, please provide valid event name");
        } else {
            NotificationServiceOuterClass.GetLatestOffsetByKeyRequest request =
                    NotificationServiceOuterClass.GetLatestOffsetByKeyRequest.newBuilder()
                            .setNamespace(namespace)
                            .setName(event_name)
                            .build();
            NotificationServiceOuterClass.GetLatestOffsetResponse response =
                    notificationServiceStub.getLatestOffsetByKey(request);
            return parseLatestOffsetFromResponse(response);
        }
    }

    public long parseLatestOffsetFromResponse(
            NotificationServiceOuterClass.GetLatestOffsetResponse response) throws Exception {
        if (response.getReturnCode()
                .equals(NotificationServiceOuterClass.ReturnStatus.ERROR.toString())) {
            throw new Exception(response.getReturnMsg());
        } else {
            return response.getOffset();
        }
    }

    public AtomicInteger getSequenceNum() {
        return this.sequenceNum;
    }

    public Long getClientId() {
        return clientId;
    }

    public void close() throws Exception {
        if (this.clientId >= 0) {
            NotificationServiceOuterClass.ClientIdRequest request =
                    NotificationServiceOuterClass.ClientIdRequest.newBuilder()
                            .setClientId(this.clientId)
                            .build();
            NotificationServiceOuterClass.CommonResponse response =
                    notificationServiceStub.deleteClient(request);
            if (response.getReturnCode() != NotificationServiceOuterClass.ReturnStatus.SUCCESS) {
                throw new Exception(response.getReturnMsg());
            }
        }
        disableHighAvailability();
        channel.shutdown();
        try {
            channel.awaitTermination(5000, TimeUnit.MILLISECONDS);
        } catch (InterruptedException ex) {
            logger.error("gRPC channel shutdown interrupted");
        }
    }
}
