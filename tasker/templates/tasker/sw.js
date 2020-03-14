"use strict";

self.importScripts('{% url "jsi18n" %}');

self.addEventListener('push', function (event) {
    var data = event.data.json();

    if (data.type === "ping") {
        console.log(data);
        const title = "PING";
        const options = {
            'body': "PING",
            'data': data,
        };
        event.waitUntil(self.registration.showNotification(title, options));
    }

    if (data.type === "handling_started_by_other") {
        const title = interpolate(gettext("%(board_label)s"), data, true);
        const options = {
            'body': interpolate(gettext("%(participant_nick)s started working on %(task_label)s"), data, true),
            'vibrate': [500, 200, 500],
            'data': data,
        };
        event.waitUntil(self.registration.showNotification(title, options));
    }

    if (data.type === "handling_completed_by_other") {
        const title = interpolate(gettext("%(board_label)s"), data, true);
        const options = {
            'body': interpolate(gettext("%(participant_nick)s finished %(task_label)s"), data, true),
            'vibrate': [300, 200, 500],
            'data': data,
        };
        event.waitUntil(self.registration.showNotification(title, options));
    }

    if (data.type === "handling_aborted_by_other") {
        const title = interpolate(gettext("%(board_label)s"), data, true);
        const options = {
            'body': interpolate(gettext("%(participant_nick)s aborted %(task_label)s"), data, true),
            'vibrate': [300, 300, 300, 300, 300, 300, 300],
            'data': data,
        };
        event.waitUntil(self.registration.showNotification(title, options));
    }

    if (data.type === "comment_posted_by_other") {
        const title = interpolate(gettext("%(board_label)s"), data, true);
        const options = {
            'body': interpolate(gettext("%(participant_nick)s commented on %(task_label)s"), data, true),
            'vibrate': [300],
            'data': data,
        };
        event.waitUntil(self.registration.showNotification(title, options));
    }

    if (data.type === "handling_running_reminder") {
        const title = interpolate(gettext("%(board_label)s"), data, true);
        const options = {
            'body': interpolate(gettext("Are you still working on %(task_label)s?"), data, true),
            'vibrate': [500, 500, 500],
            'data': data,
            'tag': 'reminder_' + data.task_path,
            'renotify': true,
            'actions': [
                {'action': 'complete', 'title': gettext("I'm done")},
                {'action': 'abort', 'title': gettext("I resigned")},
                {'action': 'dismiss', 'title': gettext("Still on it")},
            ],
        };
        event.waitUntil(self.registration.showNotification(title, options));
    }
});

self.addEventListener('notificationclick', function (event) {
    if (["handling_started_by_other", "handling_completed_by_other", "handling_aborted_by_other", "comment_posted_by_other"].includes(event.notification.data.type)) {
        event.notification.close();
        event.waitUntil(open_url(new URL(event.notification.data.task_path, self.location.origin).href));
    }

    if (event.notification.data.type === "handling_running_reminder") {
        if (event.action) {
            if (event.action === 'dismiss') {
                event.notification.close();
            }
            if (event.action === 'complete') {
                event.waitUntil(
                    fetch(event.notification.data.complete_path)
                        .then(function (response) {
                            event.notification.close();
                            return open_url(new URL(event.notification.data.task_path, self.location.origin).href);
                        }));
            }
            if (event.action === 'abort') {
                event.waitUntil(
                    fetch(event.notification.data.abort_path)
                        .then(function (response) {
                            event.notification.close();
                            return open_url(new URL(event.notification.data.task_path, self.location.origin).href);
                        }));
            }
        } else {
            event.notification.close();
            event.waitUntil(open_url(new URL(event.notification.data.task_path, self.location.origin).href));
        }
    }
});

function open_url(url) {
    return clients.matchAll({
        type: 'window',
        includeUncontrolled: true,
    }).then(function (windowClients) {
        let matchingClient = null;

        for (let i = 0; i < windowClients.length; i++) {
            if (windowClients[i].url === url) {
                matchingClient = windowClients[i];
                break;
            }
        }

        if (matchingClient) {
            return matchingClient.focus();
        } else {
            return clients.openWindow(url);
        }
    });
}
