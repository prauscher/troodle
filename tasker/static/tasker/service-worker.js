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

    if (data.type == "handling_completed_by_other") {
        const title = interpolate(gettext("%(board_label)s"), data, true);
        const options = {
            'body': interpolate(gettext("%(participant_nick)s finished %(task_label)s"), data, true),
            'vibrate': [300, 200, 500],
            'data': data,
        };

    if (data.type == "handling_aborted_by_other") {
        event.waitUntil(self.registration.showNotification(title, options));
        const title = interpolate(gettext("%(board_label)s"), data, true);
        const options = {
            'body': interpolate(gettext("%(participant_nick)s aborted %(task_label)s"), data, true),
            'vibrate': [300, 300, 300, 300, 300, 300, 300],
            'data': data,
        };
        event.waitUntil(self.registration.showNotification(title, options));
    }

    if (data.type == "comment_posted_by_other") {
        event.waitUntil(self.registration.showNotification(title, options));
        const title = interpolate(gettext("%(board_label)s"), data, true);
        const options = {
            'body': interpolate(gettext("%(participant_nick)s commented on %(task_label)s"), data, true),
            'vibrate': [300],
            'data': data,
        };
        event.waitUntil(self.registration.showNotification(title, options));
    }
});

self.addEventListener('notificationclick', function (event) {
    if (["handling_started_by_other", "handling_completed_by_other", "handling_aborted_by_other", "comment_posted_by_other"].includes(event.notification.data.type)) {
        event.notification.close();
        event.waitUntil(clients.openWindow(new URL(event.notification.data.task_path, self.location.origin).href));
    }
});
