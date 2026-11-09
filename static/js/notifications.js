
document.addEventListener("DOMContentLoaded", function () {

    const badge = document.getElementById(
        "notification-count"
    );

    const list = document.getElementById(
        "notification-list"
    );

    const markAllButton = document.getElementById(
        "mark-all-read"
    );

    if (!badge || !list) {
        return;
    }

    let unreadCount = 0;

    // =====================================
    // CSRF TOKEN
    // =====================================

    function getCookie(name) {

        let cookieValue = null;

        if (document.cookie) {

            document.cookie.split(";").forEach(function (cookie) {

                cookie = cookie.trim();

                if (cookie.startsWith(name + "=")) {

                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );

                }

            });

        }

        return cookieValue;
    }


    // =====================================
    // UPDATE BADGE
    // =====================================

    function updateBadge(count) {

        unreadCount = count;

        badge.textContent = count;

        badge.style.display = count > 0
            ? "inline-block"
            : "none";
    }


    // =====================================
    // CREATE NOTIFICATION ELEMENT
    // =====================================

    function addNotification(item, prepend = true) {

        const wrapper = document.createElement("div");

        wrapper.className =
            "border-bottom py-2 notification-item";

        wrapper.dataset.id = item.id;

        if (!item.is_read) {

            wrapper.classList.add("bg-light");

        }

        const title = document.createElement("strong");

        title.textContent = item.title;

        const message = document.createElement("p");

        message.className = "small mb-1";

        message.textContent = item.message;

        const time = document.createElement("small");

        time.className = "text-muted";

        time.textContent = new Date(
            item.created_at
        ).toLocaleString();

        wrapper.appendChild(title);

        wrapper.appendChild(message);

        wrapper.appendChild(time);

        wrapper.addEventListener("click", function () {

            markAsRead(item.id, function () {

                if (item.url) {

                    window.location.href = item.url;

                }

            });

        });

        if (prepend) {

            list.prepend(wrapper);

        } else {

            list.appendChild(wrapper);

        }

    }


    // =====================================
    // LOAD EXISTING NOTIFICATIONS
    // =====================================

    async function loadNotifications() {

        try {

            const response = await fetch(
                "/notifications/"
            );

            if (!response.ok) {
                throw new Error("Unable to load notifications.");
            }

            const data = await response.json();

            list.replaceChildren();

            if (data.notifications.length === 0) {

                const empty = document.createElement("p");

                empty.className =
                    "text-muted text-center";

                empty.textContent =
                    "No notifications available.";

                list.appendChild(empty);

            } else {

                data.notifications.forEach(function (item) {

                    addNotification(item, false);

                });

            }

            updateBadge(data.unread_count);

        } catch (error) {

            console.error(error);

        }

    }


    // =====================================
    // MARK ONE NOTIFICATION AS READ
    // =====================================

    async function markAsRead(id, callback) {

        try {

            const response = await fetch(
                `/notifications/mark-read/${id}/`,
                {

                    method: "POST",

                    headers: {

                        "X-CSRFToken": getCookie("csrftoken"),

                    },

                }
            );

            if (!response.ok) {
                throw new Error("Unable to mark notification as read.");
            }

            const item = document.querySelector(
                `.notification-item[data-id="${id}"]`
            );

            if (item) {

                item.classList.remove("bg-light");

            }

            updateBadge(Math.max(0, unreadCount - 1));

            if (callback) {
                callback();
            }

        } catch (error) {

            console.error(error);

        }

    }


    // =====================================
    // MARK ALL AS READ
    // =====================================

    if (markAllButton) {

        markAllButton.addEventListener(
            "click",
            async function () {

                try {

                    const response = await fetch(
                        "/notifications/mark-all-read/",
                        {

                            method: "POST",

                            headers: {

                                "X-CSRFToken": getCookie("csrftoken"),

                            },

                        }
                    );

                    if (!response.ok) {
                        throw new Error("Unable to mark notifications as read.");
                    }

                    document.querySelectorAll(
                        ".notification-item"
                    ).forEach(function (item) {

                        item.classList.remove("bg-light");

                    });

                    updateBadge(0);

                } catch (error) {

                    console.error(error);

                }

            }
        );

    }


    // =====================================
    // REAL-TIME WEBSOCKET CONNECTION
    // =====================================

    const protocol = window.location.protocol === "https:"
        ? "wss:"
        : "ws:";

    const socket = new WebSocket(
        `${protocol}//${window.location.host}/ws/notifications/`
    );


    socket.onopen = function () {

        console.log("Notification connection established.");

    };


    socket.onmessage = function (event) {

        const notification = JSON.parse(event.data);

        notification.is_read = false;

        const emptyMessage = list.querySelector("p");

        if (
            emptyMessage &&
            emptyMessage.textContent === "No notifications available."
        ) {

            list.replaceChildren();

        }

        addNotification(notification);

        updateBadge(unreadCount + 1);

    };


    socket.onclose = function () {

        console.log("Notification connection closed.");

    };


    socket.onerror = function (error) {

        console.error("Notification WebSocket error:", error);

    };


    // Initial load
    loadNotifications();

});
