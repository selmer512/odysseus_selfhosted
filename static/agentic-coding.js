(function(){
  var log = document.getElementById('agentic-log');
  var status = document.getElementById('agentic-status');
  function show(value){
    if(!log) return;
    log.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  }
  async function api(path, options){
    var response = await fetch('/api/agentic-coding' + path, Object.assign({
      headers: {'Content-Type': 'application/json'}
    }, options || {}));
    var data = await response.json().catch(function(){ return {}; });
    if(!response.ok){ throw new Error(data.detail || data.error || response.status); }
    return data;
  }
  async function refresh(){
    try{
      var health = await api('/health');
      if(status) status.textContent = health.ok ? 'Backend online' : 'Backend unavailable';
      var profiles = await api('/model-profiles');
      show({health: health, profiles: profiles.profiles || []});
    }catch(error){
      if(status) status.textContent = 'Backend blocked or offline';
      show(String(error));
    }
  }
  window.agenticCodingRefresh = refresh;
  refresh();
})();
