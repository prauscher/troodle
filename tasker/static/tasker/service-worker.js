self.importScripts('/jsi18n.js')

self.addEventListener('install', function(event) {
    console.log(gettext('Hello ServiceWorker'));
});

self.addEventListener('push', function (event) {
    console.log(gettext('Received Push'), event.data.json());
});
