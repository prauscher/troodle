{% load static %}

if (!("serviceWorker" in navigator)) {
    console.log("serviceWorker not supported.");
}

if (!("PushManager" in window)) {
    console.log("PushManager not supported.");
}

if ("serviceWorker" in navigator && "PushManager" in window) {
    var serviceWorker = navigator.serviceWorker.register("{% static "tasker/service-worker.js" %}");

    function _storeSubscription(pushSubscription) {
        $.post('{% url "webpush_register" %}', {
            subscription: JSON.stringify(pushSubscription),
        });
    }

    serviceWorker.then(function (registration) {
        registration.pushManager.getSubscription().then(function (pushSubscription) {
            isSubscribed = !(pushSubscription === null);
            if (isSubscribed) {
                _storeSubscription(pushSubscription);
            }
        });
    })

    function requestPush() {
        serviceWorker.then(function (registration) {
            const subscribeOptions = {
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array('{{ push_pubkey }}'),
            };
            return registration.pushManager.subscribe(subscribeOptions);
        }).then(function (pushSubscription) {
            _storeSubscription(pushSubscription);
        }).catch(function (error) {
            console.error(error);
        });
    }
} else {
    function requestPush() {
        return false;
    }
}

/**
 * urlBase64ToUint8Array
 * 
 * @param {string} base64String a public vavid key
 */
function urlBase64ToUint8Array(base64String) {
    var padding = '='.repeat((4 - base64String.length % 4) % 4);
    var base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    var rawData = window.atob(base64);
    var outputArray = new Uint8Array(rawData.length);

    for (var i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}
