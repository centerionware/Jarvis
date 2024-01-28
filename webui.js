var toggle_query_form = function() {
  document.querySelectorAll('.query_form').forEach((el) => {
    if( !el.classList.contains('activated') ) {
      el.classList.add('activated');
    }
  });
}

function connect(ws) {
    ws = new WebSocket('wss://'+window.location.hostname+'/ws');
    ws.onopen = function() {
      console.log('WebSocket Client Connected');
    };
  
    ws.onmessage = function(e) {
      // Dump the message into body->response
      document.getElementById('response').innerHTML = e.data;

      toggle_query_form();

      document.querySelector(".query_input").value = "";
      console.log('Message:', e.data);
    };
  
    ws.onclose = function(e) {
      console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
      setTimeout(function() {
        connect(window.ws);
      }, 1000);
    };
  
    ws.onerror = function(err) {
      console.error('Socket encountered error: ', err.message, 'Closing socket');
      ws.close();
    };
    return ws
}

window.ws = connect(window.ws);
// Form has one input field named 'q', send it via websocket and prevent default form action

var websocket_submit = function() {
    
    window.ws.send(JSON.stringify({
        'message': document.getElementById('q').value
    }));
    document.getElementById('q').value = '';
    // Find the object with the class query_form and add the class 'activated' to it if it doesn't have it
    toggle_query_form();
    return false
}
