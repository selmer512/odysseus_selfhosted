(function(){
  var log = document.getElementById('agentic-log');
  var status = document.getElementById('agentic-status');
  var workspaceList = document.getElementById('workspace-list');
  var workspaceSelect = document.getElementById('workspace-select');
  var profileSelect = document.getElementById('profile-select');
  var latestScaffold = null;
  var latestRun = null;

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

  function option(value, label){
    return '<option value="' + String(value || '').replace(/"/g, '&quot;') + '">' + String(label || value || '') + '</option>';
  }

  function renderWorkspaces(rows){
    rows = rows || [];
    if(workspaceList){
      workspaceList.innerHTML = rows.length ? rows.map(function(row){
        return '<div class="mini-card"><b>' + (row.title || row.path || row.id) + '</b><div class="muted">' + (row.path || '') + '</div></div>';
      }).join('') : '<p class="muted">No workspaces registered yet.</p>';
    }
    if(workspaceSelect){
      workspaceSelect.innerHTML = rows.map(function(row){ return option(row.id, row.title || row.path || row.id); }).join('');
    }
  }

  async function refresh(){
    try{
      var health = await api('/health');
      if(status) status.textContent = health.ok ? 'Backend online' : 'Backend unavailable';
      var profiles = await api('/model-profiles');
      if(profileSelect){
        profileSelect.innerHTML = (profiles.profiles || []).map(function(profile){ return option(profile.id, profile.label); }).join('');
      }
      var workspaces = await api('/workspaces');
      renderWorkspaces(workspaces.workspaces || []);
      show({health: health, profiles: profiles.profiles || [], workspaces: workspaces.workspaces || []});
    }catch(error){
      if(status) status.textContent = 'Backend blocked or offline';
      show(String(error));
    }
  }

  async function createWorkspace(){
    try{
      var path = document.getElementById('workspace-path').value;
      var title = document.getElementById('workspace-title').value;
      var created = await api('/workspaces', {method:'POST', body: JSON.stringify({path:path, title:title || null})});
      await refresh();
      show(created);
    }catch(error){ show(String(error)); }
  }

  async function createScaffold(){
    try{
      var workspaceId = workspaceSelect && workspaceSelect.value;
      var goal = document.getElementById('scaffold-goal').value;
      var model = profileSelect && profileSelect.value;
      var scaffold = await api('/scaffolds', {method:'POST', body: JSON.stringify({workspace_id:workspaceId, user_goal:goal, model:model || null})});
      latestScaffold = scaffold.id;
      latestRun = null;
      show(scaffold);
    }catch(error){ show(String(error)); }
  }

  async function approveScaffold(){
    try{
      if(!latestScaffold){ throw new Error('Create a scaffold first.'); }
      show(await api('/scaffolds/' + latestScaffold + '/approve', {method:'POST'}));
    }catch(error){ show(String(error)); }
  }

  async function createRun(){
    try{
      if(!latestScaffold){ throw new Error('Create and approve a scaffold first.'); }
      var run = await api('/runs', {method:'POST', body: JSON.stringify({scaffold_id: latestScaffold})});
      latestRun = run.id;
      show(run);
    }catch(error){ show(String(error)); }
  }

  async function executeRun(){
    try{
      if(!latestRun){ throw new Error('Create a run first.'); }
      var run = await api('/runs/' + latestRun + '/execute', {method:'POST'});
      var artifacts = await api('/runs/' + latestRun + '/artifacts');
      show({run: run, artifacts: artifacts.artifacts || []});
    }catch(error){ show(String(error)); }
  }

  window.agenticCodingRefresh = refresh;
  window.agenticCreateWorkspace = createWorkspace;
  window.agenticCreateScaffold = createScaffold;
  window.agenticApproveScaffold = approveScaffold;
  window.agenticCreateRun = createRun;
  window.agenticExecuteRun = executeRun;
  refresh();
})();
