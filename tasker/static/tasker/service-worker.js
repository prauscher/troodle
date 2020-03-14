"use strict";

self.importScripts('/jsi18n.js')

self.addEventListener('push', function (event) {
    var data = event.data.json();

    if (data.type == "handling_started_by_other") {
        const title = interpolate(gettext("%(board_label)s"), data, true);
        const options = {
            'body': interpolate(gettext("%(participant_nick)s started working on %(task_label)s"), data, true),
            'vibrate': [500, 200, 500],
            'data': data,
        };
        event.waitUntil(self.registration.showNotification(title, options));
    }

    if (data.type == "handling_stopped_by_other") {
        if (data.success) {
            const title = interpolate(gettext("%(board_label)s"), data, true);
            const options = {
                'body': interpolate(gettext("%(participant_nick)s finished %(task_label)s"), data, true),
                'vibrate': [300, 200, 500],
                'data': data,
            };
            event.waitUntil(self.registration.showNotification(title, options));
        } else {
            const title = interpolate(gettext("%(board_label)s"), data, true);
            const options = {
                'body': interpolate(gettext("%(participant_nick)s aborted %(task_label)s"), data, true),
                'vibrate': [500, 200, 300],
                'data': data,
            };
            event.waitUntil(self.registration.showNotification(title, options));
        }
    }
});

self.addEventListener('notificationclick', function (event) {
    if (event.notification.data.type == "handling_started_by_other") {
        event.notification.close();
        event.waitUntil(clients.openWindow(new URL(event.notification.data.task_path, self.location.origin).href));
    }

    if (event.notification.data.type == "handling_stopped_by_other") {
        event.notification.close();
        event.waitUntil(clients.openWindow(new URL(event.notification.data.task_path, self.location.origin).href));
    }
});
