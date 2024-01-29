var toggle_query_form = function() {
  document.querySelectorAll('.query_form').forEach((el) => {
    if( !el.classList.contains('activated') ) {
      el.classList.add('activated');
    }
  });
}
// listen for popstate event, fired e.g. after using browser back button
window.addEventListener('popstate', (event) => updateDisplay(event.state));

// listen for load event, in case we navigate away and then go back
window.addEventListener('load', () => updateDisplay(history.state), false);

function updateDisplay(state) {
  if (state) {
    parseResponse( state.data );
  } else {
    
  }
}
function parseResponse(data) {
    loaded = JSON.parse(data);
    document.getElementById('response').innerHTML = loaded.result;
    the_prompt = JSON.parse(loaded.prompt);
    content = JSON.parse(the_prompt.messages[0].content)
    parseSearchResults(content);
    toggle_query_form();
}
function parseSearchResults(content) {
  searxng_div = document.createElement('div');
  new_header = document.createElement('h3');
  new_header.innerHTML = "Non-AI Results from SearXNG:"
  searxng_div.appendChild(new_header);
  content.results.forEach((el) => { 
    new_div = document.createElement('div');
    new_link = document.createElement('a');
    new_link.href = el.url;
    new_link.innerHTML = el.title;
    new_paragraph = document.createElement('p');
    new_paragraph.innerHTML = el.content;
    new_div.appendChild(new_link);
    new_div.appendChild(new_paragraph);
    new_img = document.createElement('img');
    new_img.src = el.img_src != null ? el.img_src : "";
    new_div.appendChild(new_img);
    searxng_div.appendChild(new_div);
  });
  document.getElementById('response').appendChild(searxng_div);
}
var show_connect_message = false;
function connect(ws) {
    ws = new WebSocket('wss://'+window.location.hostname+'/ws');
    ws.onopen = function() {
      window.ws = ws;
      console.log('WebSocket Client Connected');
      if(show_connect_message) {
        document.getElementById('response').innerHTML = '<div class="error">WebSocket Client Connected</div>';
      } else show_connect_message = true;
    };
  
    ws.onmessage = function(e) {
      // Dump the message into body->response
      if(e.data == "Searching..."){ 
        document.getElementById('response').innerHTML = '<div class="error">Searching...<img src="https://media1.tenor.com/m/TgPXdDAfIeIAAAAd/gawr-gura-gura.gif"/></div>';
        toggle_query_form();
        return
      }
      loaded = JSON.parse(e.data);
      if( loaded.status != "completed" ) {
        nd = document.createElement('div');
        nd.innerHTML = "While Jarvis is thinking, here's the results from SearXNG:";
        document.getElementById('response').appendChild(nd);
        parseSearchResults(JSON.parse(loaded.result));
        return
      }
      parseResponse(e.data);
      if( loaded.status == "completed" ) {
        history.pushState({data: e.data}, document.getElementById('q').placeholder, '?q='+document.getElementById('q').placeholder);
        document.querySelector(".query_input").value = "";
      }
      console.log('Message:', e.data);
    };
  
    ws.onclose = function(e) {
      console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
      document.getElementById('response').innerHTML = '<div class="error">Socket is closed. Reconnect will be attempted in 1 second. ' + e.reason+"</div>";
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
    document.getElementById('q').placeholder = document.getElementById('q').value;
    document.getElementById('q').value = '';
    
    // Find the object with the class query_form and add the class 'activated' to it if it doesn't have it
    toggle_query_form();
    return false
}
