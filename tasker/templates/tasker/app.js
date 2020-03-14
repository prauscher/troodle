{% load static %}

if (!("serviceWorker" in navigator)) {
    console.log("serviceWorker not supported.");
}

if (!("PushManager" in window)) {
    console.log("PushManager not supported.");
}

if ("serviceWorker" in navigator && "PushManager" in window) {
    var serviceWorker = navigator.serviceWorker.register("{% url 'jssw' %}");

    function _storeSubscription(pushSubscription) {
        return new Promise(function (resolve, reject) {
            $.post('{% url "webpush_register" %}', {
                subscription: JSON.stringify(pushSubscription),
            }, function () { resolve(); });
        });
    }

    serviceWorker.then(function (registration) {
        registration.pushManager.getSubscription().then(function (pushSubscription) {
            isSubscribed = !(pushSubscription === null);
            if (isSubscribed && Math.random() < 0.1) {
                _storeSubscription(pushSubscription);
            }
        });
    })

    function requestPush() {
        return serviceWorker.then(function (registration) {
            const subscribeOptions = {
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array('{{ push_pubkey }}'),
            };
            return registration.pushManager.subscribe(subscribeOptions);
        });
    }

    function requestPushAndStore() {
        return Promise(function (resolve, reject) {
            requestPush().then(function (pushSubscription) {
                _storeSubscription(pushSubscription).then(function () {
                    resolve();
                });
            }).catch(reject);
        });
    }
} else {
    function requestPush() {
        return Promise(function (resolve, reject) {
            resolve();
        });
    }

    function requestPushAndStore() {
        return Promise(function (resolve, reject) {
            resolve();
        });
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
