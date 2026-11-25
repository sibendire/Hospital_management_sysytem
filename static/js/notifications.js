
/*
 * =========================================================
 * MediCare HMS - Centralized Live Notifications
 * =========================================================
 *
 * HTTP ENDPOINTS:
 * GET  /notifications/
 * POST /notifications/mark-read/<id>/
 * POST /notifications/mark-all-read/
 *
 * WEBSOCKET:
 * WS   /ws/notifications/
 *
 * EXPECTED GET RESPONSE:
 * {
 *     "notifications": [],
 *     "unread_count": 0
 * }
 *
 * SUPPORTED WEBSOCKET PAYLOADS:
 * {
 *     "id": 1,
 *     "title": "New Laboratory Request",
 *     "message": "A new laboratory request is available.",
 *     "notification_type": "LAB_REQUEST",
 *     "url": "/laboratory/"
 * }
 *
 * OR:
 * {
 *     "notification": {
 *         "id": 1,
 *         "title": "New Laboratory Request",
 *         "message": "A new laboratory request is available."
 *     }
 * }
 * =========================================================
 */

(() => {
    "use strict";

    /* =====================================================
       CONFIGURATION
       ===================================================== */

    const CONFIG = {
        listUrl: "/notifications/",

        markReadUrl: (id) =>
            `/notifications/mark-read/${encodeURIComponent(id)}/`,

        markAllReadUrl: "/notifications/mark-all-read/",

        websocketPath: "/ws/notifications/",

        reconnectBaseMs: 1000,
        reconnectMaxMs: 30000,

        reconnectJitterMs: 500,

        refreshIntervalMs: 60000,

        maxNotifications: 100
    };


    /* =====================================================
       APPLICATION STATE
       ===================================================== */

    const state = {
        socket: null,

        reconnectTimer: null,

        refreshTimer: null,

        reconnectAttempt: 0,

        unreadCount: 0,

        notifications: new Map(),

        loading: false,

        connected: false,

        initialized: false,

        destroyed: false,

        markingAllRead: false
    };


    /* =====================================================
       HTML ELEMENTS
       ===================================================== */

    const elements = {
        toggle: null,
        dropdown: null,
        badge: null,
        list: null,
        markAll: null
    };


    /* =====================================================
       INITIALIZATION
       ===================================================== */

    document.addEventListener("DOMContentLoaded", init);


    function init() {

        if (state.initialized) {
            return;
        }

        state.initialized = true;

        elements.toggle =
            document.getElementById("notification-toggle");

        elements.dropdown =
            document.getElementById("notification-dropdown");

        elements.badge =
            document.getElementById("notification-count");

        elements.list =
            document.getElementById("notification-list");

        elements.markAll =
            document.getElementById("mark-all-read");


        if (!elements.badge || !elements.list) {

            console.warn(
                "MediCare HMS: Notification HTML elements were not found."
            );

            return;
        }


        setupDropdown();

        setupMarkAllButton();

        updateBadge();


        // Load existing notifications first.
        // Connect to WebSocket after loading.

        loadNotifications()
            .finally(() => {

                connectWebSocket();

                startPeriodicRefresh();

            });


        // Reconnect and refresh when the browser tab becomes visible.

        document.addEventListener(
            "visibilitychange",
            handleVisibilityChange
        );


        // Clean up when the page is unloaded.

        window.addEventListener(
            "beforeunload",
            cleanup
        );

    }


    /* =====================================================
       DROPDOWN MANAGEMENT
       ===================================================== */

    function setupDropdown() {

        if (!elements.toggle || !elements.dropdown) {
            return;
        }


        elements.toggle.addEventListener(
            "click",
            (event) => {

                event.preventDefault();

                event.stopPropagation();

                const isOpen =
                    elements.dropdown.classList.toggle("show");

                elements.toggle.setAttribute(
                    "aria-expanded",
                    String(isOpen)
                );

            }
        );


        document.addEventListener(
            "click",
            (event) => {

                if (
                    !elements.dropdown.contains(event.target) &&
                    !elements.toggle.contains(event.target)
                ) {

                    closeDropdown();

                }

            }
        );


        document.addEventListener(
            "keydown",
            (event) => {

                if (event.key === "Escape") {

                    closeDropdown();

                }

            }
        );

    }


    function closeDropdown() {

        if (!elements.dropdown || !elements.toggle) {
            return;
        }

        elements.dropdown.classList.remove("show");

        elements.toggle.setAttribute(
            "aria-expanded",
            "false"
        );

    }


    /* =====================================================
       CSRF TOKEN
       ===================================================== */

    function getCookie(name) {

        const cookie = document.cookie
            .split(";")
            .map((part) => part.trim())
            .find((part) => part.startsWith(`${name}=`));


        return cookie
            ? decodeURIComponent(
                cookie.substring(name.length + 1)
            )
            : "";

    }


    function csrfToken() {

        return (

            getCookie("csrftoken") ||

            document.querySelector(
                'input[name="csrfmiddlewaretoken"]'
            )?.value ||

            ""

        );

    }


    /* =====================================================
       HTTP REQUESTS
       ===================================================== */

    async function requestJson(url, options = {}) {

        const method =
            (options.method || "GET").toUpperCase();


        const headers = {

            "X-Requested-With": "XMLHttpRequest",

            "Accept": "application/json",

            ...(options.headers || {})

        };


        if (method !== "GET" && method !== "HEAD") {

            const token = csrfToken();

            if (token) {

                headers["X-CSRFToken"] = token;

            }

        }


        const response = await fetch(url, {

            credentials: "same-origin",

            ...options,

            method,

            headers

        });


        if (!response.ok) {

            let errorMessage =
                `Request failed (${response.status})`;


            try {

                const errorData = await response.json();

                errorMessage =
                    errorData.error ||
                    errorData.message ||
                    errorMessage;

            } catch (_) {

                // Keep the original HTTP error message.

            }


            throw new Error(errorMessage);

        }


        if (response.status === 204) {
            return {};
        }


        return response.json();

    }


    /* =====================================================
       NORMALIZE NOTIFICATION
       ===================================================== */

    function normalizeNotification(raw) {

        if (
            !raw ||
            raw.id === undefined ||
            raw.id === null
        ) {

            return null;

        }


        return {

            id: String(raw.id),

            title: raw.title || "Notification",

            message: raw.message || "",

            type:
                raw.notification_type ||
                raw.type ||
                "",

            source_module:
                raw.source_module || "",

            reference_id:
                raw.reference_id ?? null,

            url:
                raw.url || "",

            created_at:
                raw.created_at || "",

            is_read:
                raw.is_read === true ||
                raw.is_read === 1 ||
                raw.is_read === "true"

        };

    }


    /* =====================================================
       LOAD NOTIFICATIONS
       ===================================================== */

    async function loadNotifications() {

        if (state.loading || state.destroyed) {
            return;
        }


        state.loading = true;


        try {

            const data =
                await requestJson(CONFIG.listUrl);


            const items =
                Array.isArray(data.notifications)
                    ? data.notifications
                    : [];


            // Preserve notifications received over WebSocket
            // while the HTTP request was in progress.

            const liveNotifications = new Map(
                state.notifications
            );


            const refreshedNotifications = new Map();


            items.forEach((raw) => {

                const notification =
                    normalizeNotification(raw);

                if (!notification) {
                    return;
                }


                // Preserve newer local read state when possible.

                const existing =
                    liveNotifications.get(notification.id);


                if (existing && existing.is_read) {

                    notification.is_read = true;

                }


                refreshedNotifications.set(
                    notification.id,
                    notification
                );

            });


            // Add notifications received during the request
            // that were not included in the HTTP response.

            liveNotifications.forEach(
                (notification, id) => {

                    if (!refreshedNotifications.has(id)) {

                        refreshedNotifications.set(
                            id,
                            notification
                        );

                    }

                }
            );


            state.notifications =
                refreshedNotifications;


            // Keep the newest notifications first.

            sortNotifications();


            // Remove excess notifications from the display cache.

            trimNotifications();


            // Calculate unread count from the synchronized list.

            state.unreadCount = [
                ...state.notifications.values()
            ].filter(
                (notification) => !notification.is_read
            ).length;


            renderNotifications();

            updateBadge();


        } catch (error) {

            console.error(
                "MediCare HMS: Unable to load notifications:",
                error
            );


            if (!state.notifications.size) {

                showMessage(
                    "Unable to load notifications. Please try again."
                );

            }


        } finally {

            state.loading = false;

        }

    }


    /* =====================================================
       SORT NOTIFICATIONS
       ===================================================== */

    function sortNotifications() {

        const sorted = [
            ...state.notifications.values()
        ].sort((a, b) => {

            const dateA =
                new Date(a.created_at).getTime() || 0;

            const dateB =
                new Date(b.created_at).getTime() || 0;

            return dateB - dateA;

        });


        state.notifications = new Map(

            sorted.map((notification) => [
                notification.id,
                notification
            ])

        );

    }


    /* =====================================================
       LIMIT NOTIFICATION CACHE
       ===================================================== */

    function trimNotifications() {

        const entries = [
            ...state.notifications.entries()
        ];

        if (entries.length <= CONFIG.maxNotifications) {
            return;
        }


        state.notifications = new Map(

            entries.slice(0, CONFIG.maxNotifications)

        );

    }


    /* =====================================================
       RENDER NOTIFICATIONS
       ===================================================== */

    function renderNotifications() {

        if (!elements.list) {
            return;
        }


        elements.list.replaceChildren();


        const notifications = [
            ...state.notifications.values()
        ];


        if (!notifications.length) {

            showMessage("No notifications yet.");

            return;

        }


        notifications.forEach((notification) => {

            elements.list.appendChild(

                createNotificationElement(notification)

            );

        });

    }


    /* =====================================================
       CREATE NOTIFICATION ELEMENT
       ===================================================== */

    function createNotificationElement(notification) {

        const item = document.createElement("div");


        item.className =
            `notification-item ${
                notification.is_read
                    ? "is-read"
                    : "is-unread bg-light"
            }`;


        item.dataset.notificationId =
            notification.id;


        item.setAttribute("role", "button");

        item.setAttribute("tabindex", "0");


        item.setAttribute(
            "aria-label",
            `${notification.title}. ${notification.message}`
        );


        const title = document.createElement("div");

        title.className =
            "notification-title fw-semibold";

        title.textContent =
            notification.title;


        const message = document.createElement("div");

        message.className =
            "notification-message";

        message.textContent =
            notification.message;


        const date = document.createElement("small");

        date.className =
            "notification-date text-muted";

        date.textContent =
            formatDate(notification.created_at);


        item.append(
            title,
            message,
            date
        );


        item.addEventListener(
            "click",
            () => {

                openNotification(notification);

            }
        );


        item.addEventListener(
            "keydown",
            (event) => {

                if (
                    event.key === "Enter" ||
                    event.key === " "
                ) {

                    event.preventDefault();

                    openNotification(notification);

                }

            }
        );


        return item;

    }


    /* =====================================================
       EMPTY / ERROR MESSAGE
       ===================================================== */

    function showMessage(message) {

        if (!elements.list) {
            return;
        }


        elements.list.replaceChildren();


        const empty = document.createElement("div");

        empty.className =
            "notification-empty text-muted p-3 text-center";

        empty.textContent = message;


        elements.list.appendChild(empty);

    }


    /* =====================================================
       FORMAT DATE
       ===================================================== */

    function formatDate(value) {

        if (!value) {
            return "";
        }


        const date = new Date(value);


        if (Number.isNaN(date.getTime())) {

            return String(value);

        }


        return date.toLocaleString();

    }


    /* =====================================================
       UNREAD BADGE
       ===================================================== */

    function updateBadge() {

    if (!elements.badge) {
        return;
    }

    const count = Math.max(0, state.unreadCount);

    elements.badge.textContent =
        count > 99 ? "99+" : String(count);

    // Explicitly control visibility.
    elements.badge.style.display =
        count > 0 ? "inline-flex" : "none";

    elements.badge.setAttribute(
        "aria-label",
        `${count} unread notifications`
    );

    if (elements.toggle) {

        elements.toggle.setAttribute(
            "aria-label",
            `Notifications, ${count} unread`
        );

    }
}
    /* =====================================================
       OPEN NOTIFICATION
       ===================================================== */

    async function openNotification(notification) {

        if (!notification) {
            return;
        }


        if (!notification.is_read) {

            const success =
                await markAsRead(notification.id);


            // Do not navigate if the server rejected the
            // mark-as-read operation.

            if (!success) {

                return;

            }

        }


        if (notification.url) {

            // Prevent javascript: and other unsafe schemes.

            try {

                const target =
                    new URL(
                        notification.url,
                        window.location.origin
                    );


                if (
                    target.origin !== window.location.origin ||
                    !["http:", "https:"].includes(target.protocol)
                ) {

                    console.warn(
                        "Blocked unsafe notification URL:",
                        notification.url
                    );

                    return;

                }


                window.location.assign(target.href);


            } catch (error) {

                console.error(
                    "Invalid notification URL:",
                    error
                );

            }

        }

    }


    /* =====================================================
       MARK ONE NOTIFICATION AS READ
       ===================================================== */

    async function markAsRead(id) {

        const notification =
            state.notifications.get(String(id));


        if (!notification || notification.is_read) {

            return true;

        }


        try {

            await requestJson(

                CONFIG.markReadUrl(id),

                {
                    method: "POST"
                }

            );


            notification.is_read = true;


            state.notifications.set(
                notification.id,
                notification
            );


            state.unreadCount = Math.max(
                0,
                state.unreadCount - 1
            );


            updateBadge();


            const node = elements.list.querySelector(

                `[data-notification-id="${CSS.escape(
                    notification.id
                )}"]`

            );


            if (node) {

                node.classList.remove("bg-light");

                node.classList.remove("is-unread");

                node.classList.add("is-read");

            }


            return true;


        } catch (error) {

            console.error(
                "Unable to mark notification as read:",
                error
            );


            return false;

        }

    }


    /* =====================================================
       MARK ALL NOTIFICATIONS AS READ
       ===================================================== */

    function setupMarkAllButton() {

        if (!elements.markAll) {
            return;
        }


        elements.markAll.addEventListener(
            "click",
            markAllAsRead
        );

    }


    async function markAllAsRead() {

        if (
            !elements.markAll ||
            state.markingAllRead
        ) {

            return;

        }


        state.markingAllRead = true;

        elements.markAll.disabled = true;


        try {

            await requestJson(

                CONFIG.markAllReadUrl,

                {
                    method: "POST"
                }

            );


            state.notifications.forEach(
                (notification) => {

                    notification.is_read = true;

                }
            );


            state.unreadCount = 0;


            updateBadge();


            elements.list
                .querySelectorAll(".notification-item")
                .forEach((item) => {

                    item.classList.remove(
                        "bg-light",
                        "is-unread"
                    );

                    item.classList.add("is-read");

                });


        } catch (error) {

            console.error(
                "Unable to mark all notifications as read:",
                error
            );

        } finally {

            state.markingAllRead = false;

            elements.markAll.disabled = false;

        }

    }


    /* =====================================================
       RECEIVE LIVE NOTIFICATION
       ===================================================== */

    function addLiveNotification(raw) {

        const notification =
            normalizeNotification(raw);


        if (!notification) {
            return;
        }


        // Prevent duplicate notifications.

        if (
            state.notifications.has(notification.id)
        ) {

            return;

        }


        // New live notifications are always unread.

        notification.is_read = false;


        // Add notification to local cache.

        state.notifications.set(
            notification.id,
            notification
        );


        // Keep newest notifications first.

        sortNotifications();

        trimNotifications();


        // Recalculate unread count.

        state.unreadCount = [
            ...state.notifications.values()
        ].filter(
            (item) => !item.is_read
        ).length;


        // Update the notification interface.

        renderNotifications();

        updateBadge();

    }


    /* =====================================================
       WEBSOCKET CONNECTION
       ===================================================== */

    function connectWebSocket() {

        if (state.destroyed) {
            return;
        }


        if (!("WebSocket" in window)) {

            console.warn(
                "This browser does not support WebSockets."
            );

            return;

        }


        if (
            state.socket &&
            (
                state.socket.readyState === WebSocket.OPEN ||
                state.socket.readyState === WebSocket.CONNECTING
            )
        ) {

            return;

        }


        const scheme =
            window.location.protocol === "https:"
                ? "wss"
                : "ws";


        const socketUrl =
            `${scheme}://${window.location.host}` +
            CONFIG.websocketPath;


        try {

            state.socket =
                new WebSocket(socketUrl);


        } catch (error) {

            console.error(
                "Unable to create notification WebSocket:",
                error
            );


            scheduleReconnect();

            return;

        }


        const socket = state.socket;


        socket.onopen = () => {

            if (state.socket !== socket) {
                return;
            }


            state.connected = true;

            state.reconnectAttempt = 0;


            clearReconnectTimer();


            console.info(
                "MediCare HMS: Notification WebSocket connected."
            );

        };


        socket.onmessage = (event) => {

            if (state.socket !== socket) {
                return;
            }


            try {

                const payload =
                    JSON.parse(event.data);


                // Supports both direct and wrapped payloads.

                const notification =
                    payload.notification || payload;


                addLiveNotification(notification);


            } catch (error) {

                console.error(
                    "Invalid notification WebSocket message:",
                    error
                );

            }

        };


        socket.onclose = () => {

            if (state.socket !== socket) {
                return;
            }


            state.connected = false;

            state.socket = null;


            if (!state.destroyed) {

                scheduleReconnect();

            }

        };


        socket.onerror = (error) => {

            console.error(
                "MediCare HMS: Notification WebSocket error:",
                error
            );


            // Closing the socket allows onclose to handle
            // reconnection in one place.

            if (
                socket.readyState === WebSocket.OPEN ||
                socket.readyState === WebSocket.CONNECTING
            ) {

                socket.close();

            }

        };

    }


    /* =====================================================
       WEBSOCKET RECONNECTION
       ===================================================== */

    function scheduleReconnect() {

        if (
            state.destroyed ||
            state.reconnectTimer
        ) {

            return;

        }


        const delay = Math.min(

            CONFIG.reconnectBaseMs *
                (2 ** state.reconnectAttempt),

            CONFIG.reconnectMaxMs

        );


        const jitter =
            Math.floor(
                Math.random() * CONFIG.reconnectJitterMs
            );


        state.reconnectAttempt += 1;


        state.reconnectTimer = setTimeout(

            () => {

                state.reconnectTimer = null;

                connectWebSocket();

            },

            delay + jitter

        );

    }


    function clearReconnectTimer() {

        if (state.reconnectTimer) {

            clearTimeout(state.reconnectTimer);

            state.reconnectTimer = null;

        }

    }


    /* =====================================================
       PERIODIC NOTIFICATION REFRESH
       ===================================================== */

    function startPeriodicRefresh() {

        if (state.refreshTimer) {
            return;
        }


        state.refreshTimer = setInterval(

            () => {

                if (!document.hidden) {

                    loadNotifications();

                }

            },

            CONFIG.refreshIntervalMs

        );

    }


    /* =====================================================
       HANDLE BROWSER TAB VISIBILITY
       ===================================================== */

    function handleVisibilityChange() {

        if (document.hidden) {
            return;
        }


        // Refresh notifications in case events were missed.

        loadNotifications();


        // Reconnect if the socket is unavailable.

        if (
            !state.socket ||
            state.socket.readyState === WebSocket.CLOSED
        ) {

            clearReconnectTimer();

            connectWebSocket();

        }

    }


    /* =====================================================
       CLEANUP
       ===================================================== */

    function cleanup() {

        state.destroyed = true;


        clearReconnectTimer();


        if (state.refreshTimer) {

            clearInterval(state.refreshTimer);

            state.refreshTimer = null;

        }


        if (state.socket) {

            const socket = state.socket;

            state.socket = null;

            socket.onopen = null;

            socket.onmessage = null;

            socket.onclose = null;

            socket.onerror = null;


            if (
                socket.readyState === WebSocket.OPEN ||
                socket.readyState === WebSocket.CONNECTING
            ) {

                socket.close();

            }

        }


        state.connected = false;

    }


})();
