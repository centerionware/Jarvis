function connect(ws) {
    ws = new WebSocket('wss://'+windows.location.hostname+'/ws');
    ws.onopen = function() {
      // subscribe to some channels
      ws.send(JSON.stringify({
          //.... some message the I must send when I connect ....
      }));
    };
  
    ws.onmessage = function(e) {
      // Dump the message into body->response
      document.getElementById('response').innerHTML = e.data;
      console.log('Message:', e.data);
    };
  
    ws.onclose = function(e) {
      console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
      setTimeout(function() {
        connect(ws);
      }, 1000);
    };
  
    ws.onerror = function(err) {
      console.error('Socket encountered error: ', err.message, 'Closing socket');
      ws.close();
    };
    return ws
}
var ws;
connect(ws);
// Form has one input field named 'q', send it via websocket and prevent default form action

var websocket_submit = function(e) {
    e.preventDefault();
    ws.send(JSON.stringify({
        'message': document.getElementById('message').value
    }));
    document.getElementById('message').value = '';
    // Find the object with the class query_form and add the class 'activated' to it if it doesn't have it
    if (!document.querySelector('.query_form').classList.contains('activated')) {
        document.querySelector('.query_form').classList.add('activated');
    }
}
