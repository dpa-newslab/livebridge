var lbMixin = {
    methods: {
        linkify: function (value) {
            if (!value) return ''
            value = value.toString()
            if(value.startsWith("http"))
                return '<a href="'+value+'" target="_blank">'+value+'</a>'
            return value;
        },
        displayProps: function (data) {
            var props = {};
            for(var prop in data) {
                if(["type", "label"].indexOf(prop) == -1 ) {
                    props[prop] = data[prop]
                }
            }
            return props;
        },
        getDeepCopy: function(data) {
            return JSON.parse(JSON.stringify(data))
        }
    }
}

var authFormTmpl = `
<div class="modal" tabindex="-1" role="dialog">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title"><span v-if="mode==='add'">Add</span><span v-else>Edit</span> {{ name }}</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <form>
                    <table class="table" style="with:100%;">
                        <tr v-for="(v, k) in local_auth" class="form-group">
                            <td>{{k}}</td>
                            <td><input type="text" class="form-control" :id="'form-input-'+k" v-model="local_auth[k]"></td>
                            <td>
                                <button type="button" class="btn btn-sm btn-danger" @click="removeAuthProp(k)">
                                    X</button>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <input type="text" v-model="add_key" class="form-control" placeholder="Property name">
                            </td>
                            <td>
                                <input type="text" v-model="add_value" class="form-control" placeholder="Property value">
                            </td>
                            <td>
                                <button type="button" class="btn btn-sm btn-success" @click="addAuthProp()">
                                    +</button>
                            </td>
                        </tr>
                    </table>
                </form>
            </div>
            <div class="modal-footer">
                <button v-if="mode === 'add'" type="button" class="btn btn-primary" @click="addAuth()"  data-dismiss="modal">Add</button>
                <button v-else type="button" class="btn btn-primary" @click="updateAuth()"  data-dismiss="modal">Accept changes</button>
                <button type="button" class="btn btn-secondary" @click="reset()" data-dismiss="modal">Cancel</button>
            </div>
        </div>
    </div>
</div>`

var authTmpl = `
<div v-bind:class="{ edited: edited}">
    <div class="card source">
        <h4 class="card-header">
                    {{ name }}
                    <button type="button" class="btn btn-sm btn-primary" data-toggle="modal" :data-target="'#auth-form-'+index">Edit</button>
                    <button type="button" class="btn btn-sm btn-danger" @click="removeAuth(name)">X</button>
        </h4>
        <div class="card-body">
            <div class="card-text">
                <div v-for="(v, k) in auth">
                    {{k }}: {{v}}
                </div>
            </div>
        </div>
    </div>
    <auth-form v-bind:auth="getDeepCopy(auth)" v-bind:name="name" :id="'auth-form-'+index"></auth-form>
</div>`

var targetFormTmpl = `
<div class="modal" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><strong>Source:</strong> {{ bridge.type }} / {{ bridge.label }}</h5><br/>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-header">
            <h3 class="modal-title"><span v-if="index < 0">Add</span><span v-else>Edit</span> {{ local_target.label }}</h3>
          </div>
          <div class="modal-body">
            <form>
                <table class="table" style="with:100%;">
                    <tr v-for="(v, k) in local_target" class="form-group">
                        <td>{{k}}</td>
                        <td><input type="text" class="form-control" :id="'form-input-'+k" v-model="local_target[k]"></td>
                        <td>
                            <button type="button" class="btn btn-sm btn-danger" @click="removeTargetProp(k)">
                                X</button>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="text" v-model="add_key" class="form-control" placeholder="Property name">
                        </td>
                        <td>
                            <input type="text" v-model="add_value" class="form-control" placeholder="Property value">
                        </td>
                        <td>
                            <button type="button" class="btn btn-sm btn-success" @click="addTargetProp()">
                                +</button>
                        </td>
                    </tr>
                </table>
            </form>
          </div>
          <div class="modal-footer">
            <button v-if="index < 0" type="button" class="btn btn-primary" @click="addTarget()" data-dismiss="modal">Add new target</button>
            <button v-else type="button" class="btn btn-primary" @click="updateTarget()"  data-dismiss="modal">Accept changes</button>
            <button type="button" class="btn btn-secondary" @click="reset()" data-dismiss="modal">Cancel</button>
          </div>
        </div>
      </div>
    </div>`

var bridgeFormTmpl = `
<div class="modal" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><span v-if="index < 0">Add</span><span v-else>Edit</span> {{ local_bridge.label }}</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body">
            <form>
                <table class="table" style="with:100%;">
                    <tr v-for="(v, k) in local_bridge" v-if="k !== 'targets'" class="form-group">
                        <td>{{k}}</td>
                        <td>
                            <input type="text" class="form-control" :id="'form-input-'+k" v-model="local_bridge[k]">
                        </td>
                        <td>
                            <button type="button" class="btn btn-sm btn-danger" @click="removeBridgeProp(k)">
                                X</button>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="text" v-model="add_key" class="form-control" placeholder="Property name">
                        </td>
                        <td>
                            <input type="text" v-model="add_value" class="form-control" placeholder="Property value">
                        </td>
                        <td>
                            <button type="button" class="btn btn-sm btn-success" @click="addBridgeProp()">
                                +</button>
                        </td>
                    </tr>
                </table>
            </form>
          </div>
          <div class="modal-footer">
            <button v-if="index < 0" type="button" class="btn btn-primary" @click="addBridge()" data-dismiss="modal">Create new bridge</button>
            <button v-else type="button" class="btn btn-primary" @click="updateBridge()"  data-dismiss="modal">Accept changes</button>
            <button type="button" class="btn btn-secondary" @click="reset()" data-dismiss="modal">Cancel</button>
          </div>
        </div>
      </div>
    </div>`

var targetTmpl = `
<tr class="target" v-bind:class="{edited: edited}">
    <td>|_</td>
    <td><span class="badge badge-success">{{ target.type }}</span>
    	<strong>{{ target.label }}</strong></td>
    <td>
        <div v-for="(value, key) in displayProps(target)">
            <strong>{{ key }}:</strong>  <span v-html="linkify(value)"></span>
        </div>
    </td>
    <td></td>
    <td>
        <button type="button" class="btn btn-sm btn-primary" data-toggle="modal" :data-target="'#target-form-'+bridge_index+'-'+index">Edit</button>
        <button type="button" class="btn btn-sm btn-danger" @click="removeTarget(bridge_index, index)">X</button>
        <target-form v-bind:target="getDeepCopy(target)" v-bind:bridge="bridge" v-bind:bridge_index="bridge_index" v-bind:index="index" :id="'target-form-'+bridge_index+'-'+index"></target-form>
    </td>
</tr>`

var bridgeTmpl = `
<tr class="bridge" v-bind:class="{ edited: edited}" :key="'key-'+bridge.type+'-'+index">
	<td><span class="badge badge-primary">{{ bridge.type}}</span></td>
	<td><strong>{{ bridge.label}}</strong></td>
	<td>
		<div v-for="(v, k) in displayProps(bridge)" v-if="k !== 'targets'">
			<strong>{{k }}:</strong> <span v-html="linkify(v)"></span>
		</div>
	</td>
	<td>
		<div v-for="(target, x) in bridge.targets">
			<span class="badge badge-success">{{ target.type}}</span>
		</div>
	</td>
	<td>
        <button type="button" class="btn btn-sm btn-primary" data-toggle="modal" :data-target="'#bridge-form-'+index">Edit</button>
        <button type="button" class="btn btn-sm btn-success" data-toggle="modal" :data-target="'#target-add-form-'+index" title="Add target">+</button>
        <button type="button" class="btn btn-sm btn-danger" @click="removeBridge(index)" title="Remove bridge">X</button>
        <bridge-form v-bind:bridge="getDeepCopy(bridge)" v-bind:index="index" :id="'bridge-form-'+index"></bridge-form>
        <target-form v-bind:bridge_index="index" v-bind:bridge="bridge" v-bind:index="-1" :id="'target-add-form-'+index"></target-form>
	</td>
</tr>
`

Vue.component('auth-form', {
    template: authFormTmpl,
    props: ["auth", "name", "mode"],
    data: function () {
        return {
            local_auth: (this.mode === "add") ? {} : this.auth,
            add_key: "",
            add_value: ""
        }
    },
    methods: {
        addAuth: function() {
           this.$parent.edited = true;
           this.$parent.$options.methods.addAuth(this.name, this.local_auth)
           this.reset()
        },
        updateAuth: function() {
           this.$parent.edited = true;
           this.$parent.$parent.$options.methods.updateAuth(this.local_auth, this.name)
        },
        removeAuthProp: function(key) {
            Vue.delete(this.local_auth, key)
        },
        addAuthProp: function() {
            Vue.set(this.local_auth, this.add_key, this.add_value)
            this.add_value = ""
            this.add_key = ""
        },
        reset: function() {
            if (this.mode === "add") {
                // add form
                this.local_auth = {}
            }
        }
    }
})


Vue.component('auth', {
    template: authTmpl,
    mixins: [lbMixin],
    props: ["name", "auth", "index"],
    data: function () {
        return {
            edited: false
        }
    },
    methods: {
        removeAuth: function(keyName) {
           this.$parent.$options.methods.removeAuth(keyName)
        }
    }
})

Vue.component('target-form', {
    template: targetFormTmpl,
    props: ["bridge_index", "target", "index", "bridge"],
    data: function () {
        return {
            local_target: (this.index < 0) ? {"type": "", "label": ""} : this.target,
            add_key: "",
            add_value: ""
        }
    },
    methods: {
        addTarget: function() {
            this.$parent.$parent.$options.methods.addTarget(this.bridge_index, this.local_target)
            this.reset()
        },
        updateTarget: function() {
            this.$parent.edited = true;
            this.$parent.$parent.$options.methods.updateTarget(this.bridge_index, this.local_target, this.index)
        },
        removeTargetProp: function(key) {
            Vue.delete(this.local_target, key)
        },
        addTargetProp: function() {
            Vue.set(this.local_target, this.add_key, this.add_value)
            this.add_value = ""
            this.add_key = ""
        },
        reset: function() {
            if (this.index < 0) {
                // add form
                this.local_target = {"type": "", "label": ""}
            }
        }
    }
})

Vue.component('bridge-form', {
    template: bridgeFormTmpl,
    props: ["bridge", "index"],
    data: function () {
        return {
            local_bridge: (this.index < 0) ? {"type": "", "label": ""} : this.bridge,
            add_key: "",
            add_value: ""
        }
    },
    methods: {
        addBridge: function() {
            this.$parent.$options.methods.addBridge(this.local_bridge)
            this.reset()
        },
        updateBridge: function() {
            this.$parent.edited = true;
            this.$parent.$parent.$options.methods.updateBridge(this.local_bridge, this.index)
        },
        removeBridgeProp: function(key) {
            Vue.delete(this.local_bridge, key)
        },
        addBridgeProp: function() {
            Vue.set(this.local_bridge, this.add_key, this.add_value)
            this.add_value = ""
            this.add_key = ""
        },
        reset: function() {
            if (this.index < 0) {
                // add form
                this.local_bridge = {"type": "", "label": ""}
            }
        }
    }
})

Vue.component('target', {
    template: targetTmpl,
    props: ["bridge_index", "target", "index", "bridge"],
    mixins: [lbMixin],
    data: function () {
        return {
            edited: false
        }
    },
    methods: {
        removeTarget: function(bridge_index, index) {
           this.$parent.$options.methods.removeTarget(bridge_index, index)
        }
    }
})

Vue.component('bridge', {
    template: bridgeTmpl,
    props: ["bridge", "index"],
    mixins: [lbMixin],
    data: function () {
        return {
            edited: false,
            new_target: {"type": "", "label": ""}
        }
    },
    methods: {
        removeBridge: function(index) {
           this.$parent.$options.methods.removeBridge(index)
        }
    }
})


var app = new Vue({
    el: '#content',
    data: {
        cookie_name: "lb-db",
        loginUser: null,
        loginPassword: null,
        loggedIn: true,
        control_data: {},
        control_data_orig: {},
        username: "admin",
        password: "admin",
        edited: false,
        new_auth_key: ''
    },
    mounted() {
        this.getControlData()
    },
    methods: {
        getCookie: function() {
            var name = this.cookie_name + "=";
            var ca = document.cookie.split(';');
            for(var i = 0; i < ca.length; i++) {
                var c = ca[i];
                while (c.charAt(0) == ' ') {
                    c = c.substring(1);
                }
                if (c.indexOf(name) == 0) {
                    return c.substring(name.length, c.length);
                }
            }
            return "";
        },
        login: function() {
            if (this.loginUser && this.loginPassword) {
                axios({
                  method: 'post',
                  url: '/api/v1/session',
                  data: "username="+encodeURI(this.loginUser)+"&password="+encodeURI(this.loginPassword)
                })
                .then(response => {
                    this.loggedIn = true;
                    this.getControlData();
                    this.loginUser = "";
                    this.loginPassword = "";
                })
                .catch(function (error) {
                    console.log(error);
                });
            }
			return false;
        },
		logout: function() {
			this.loggedIn = false;
			this.control_data = {}
			this.control_data_orig = {}
			document.cookie = this.cookie_name + '=; expires=Thu, 01-Jan-70 00:00:01 GMT;';
		},
        printObject: function(key, obj, depth) {
            var d = (key) ? (depth +1): depth
            if((typeof obj) == "object") {
                if (key)
                    console.log("\t".repeat(d)+key+":")
                for(var prop in obj) {
                    var val = obj[prop]
                    this.printObject(prop, val, d)
                }
            } else {
                console.log(("\t".repeat(d))+key+": "+obj)
            }
        },
        getControlData: function() {
            var cookie_token = this.getCookie();
            axios({
                method: 'get',
                url: '/api/v1/controldata'
            }).then(response => {
                this.control_data = response.data;
                this.control_data_orig = JSON.parse(JSON.stringify(response.data));
                //this.printObject("", this.control_data, -1);
            }).catch(error =>  {
                if(error.reponse)
                    console.debug(error.response.status);
                console.log(error.message);
                if(error.response.status === 401) {
                    this.loggedIn = false;
                    this.login()
                }
            });
        },
        cleanMarker: function() {
           for(var x in app.$children) {
                if(app.$children[x].edited != undefined) {
                    app.$children[x].edited = false;
                }
           }
        },
        addAuth: function(new_key, new_auth) {
            app.$set(app.control_data.auth, new_key, new_auth)
            app.new_auth_key = ""
            app.edited = true
        },
        addBridge: function(new_bridge) {
           new_bridge["targets"] = [];
           app.control_data.bridges.splice(0, 0, new_bridge)
           app.edited = true
        },
        updateBridge: function(bridge, index) {
           app.control_data.bridges.splice(index, 1, bridge)
           app.edited = true
        },
        addTarget: function(bridge_index, target) {
            var pos = app.control_data.bridges[bridge_index].targets.length;
            app.control_data.bridges[bridge_index].targets.splice(pos, 0, target)
            app.edited = false // force rerender
            app.edited = true
        },
        updateTarget: function(bridge_index, target, index) {
            app.control_data.bridges[bridge_index].targets.splice(index, 1, target)
            app.edited = true
        },
        updateAuth: function(auth, name) {
           app.$set(app.control_data.auth, name, auth)
           app.edited = true
        },
        removeAuth: function(name) {
           Vue.delete(app.control_data.auth, name)
           app.edited = true
        },
        removeTarget: function(bridge_index, index) {
            app.control_data.bridges[bridge_index].targets.splice(index, 1)
            app.edited = false
            app.edited = true
        },
        removeTargetProp: function(bridge_index, index, key) {
            Vue.delete(app.control_data.bridges[bridge_index].targets[index], key)
            app.edited = true
        },
        addTargetProp: function(bridge_index, index, key, value) {
            app.control_data.bridges[bridge_index].targets[index][key] = value
            app.edited = true
        },
        removeBridge: function(index) {
           app.control_data.bridges.splice(index, 1)
           app.edited = true
        },
        removeBridgeProp: function(index, key) {
            Vue.delete(app.control_data.bridges[index], key)
            app.edited = true
        },
        addBridgeProp: function(index, key, value) {
            app.control_data.bridges[index][key] = value
            app.edited = true
        },
        undoChanges: function() {
            this.control_data = JSON.parse(JSON.stringify(this.control_data_orig));
            app.edited = false
            this.cleanMarker();
        },
        saveNewControlData: function() {
            app.edited = false
            axios({
                method: 'put',
                url: '/api/v1/controldata',
                data: this.control_data,
                headers: {
                    "X-Auth-Token": app.token
                }
            })
            .then(response => {
                this.cleanMarker();
                alert("Data was successfully saved!")
                //this.printObject("", this.control_data, -1);
            }).catch(function (error) {
                if(error.reponse)
                    console.debug(error.response.status);
                alert("Error: "+error.response.data.error);
            });
        }
    }
})

