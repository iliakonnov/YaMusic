var ws = null;
var queue = [];

function send(msg) {
	if (ws !== null) {
		ws.send(msg);
	} else {
		queue.push(msg);
	}
}

function connect() {
	let temp = new WebSocket('ws://localhost:34438/');

	temp.onopen = function() {
		console.log("WS>Connected");
		ws = temp;
		let temp_q = queue;
		queue = [];
		for (let msg of temp_q) {
			send(msg);
		}
	};
	temp.onmessage = function(ev) {
		// Send message from server to page
		let data = JSON.parse(ev.data);
		data.YaMusic = 'Server2Extension';
		window.postMessage(data, "*");
	};
	temp.onclose = function(ev) {
		ws = null;
		console.log('Socket is closed. Reconnect will be attempted in 0.1 second.', ev.reason);
		setTimeout(connect, 0.1);
	};
	temp.onerror = function(err) {
		ws = null;
		console.error('Socket encountered error: ', err.message, 'Closing socket');
		temp.close();
	};
}

addEventListener("message", function(ev) {
	// We only accept messages from ourselves
	if (ev.source != window) return;
	if (ev.data.YaMusic != 'Extension2Server') {
		return;
	} else {
		delete ev.data.YaMusic;
	}
	// Send message from page to server
	let msg = JSON.stringify(ev.data)
	send(msg);
});

connect();

// Inject page.js to the page
function injectScript(file, node) {
	var th = document.getElementsByTagName(node)[0];
	var s = document.createElement('script');
	s.setAttribute('type', 'text/javascript');
	s.setAttribute('src', file);
	th.appendChild(s);
}
injectScript( chrome.extension.getURL('/page.js'), 'body');
