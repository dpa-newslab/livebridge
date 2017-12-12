var displayProps = function (data) {
    var props = {};
    for(var prop in data) {
        if(["type", "label"].indexOf(prop) == -1 ) {
            props[prop] = data[prop]
        }
    }
    return props;
}

var getDeepCopy = function(data) {
    return JSON.parse(JSON.stringify(data))
}

var authFormTmpl = `
<div class="modal" tabindex="-1" role="dialog">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Edit {{ name }}</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <form>
                    <table class="table" style="with:100%;">
                        <tr v-for="(v, k) in auth" class="form-group">
                            <td>{{k}}</td>
                            <td><input type="text" class="form-control" :id="'form-input-'+k" v-model="auth[k]"></td>
                        </tr>
                    </table>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-primary" @click="updateAuth(auth, name)"  data-dismiss="modal">Accept changes</button>
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
            </div>
        </div>
    </div>
</div>`

var authTmpl = `
<div v-bind:class="{ edited: edited}">
    <div class="card source">
        <h4 class="card-header">
                    {{ name }}
                    <button type="button" class="btn btn-primary" data-toggle="modal" :data-target="'#auth-form-'+index">Edit</button>
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
            <h5 class="modal-title">Edit {{target.label}}</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body">
            <form>
                <table class="table" style="with:100%;">
                    <tr v-for="(v, k) in target" class="form-group">
                        <td>{{k}}</td>
                        <td><input type="text" class="form-control" :id="'form-input-'+k" v-model="target[k]"></td>
                        <td>
                            <button type="button" class="btn btn-sm btn-danger" @click="removeTargetProp(bridge_index, index, k)">
                                X</button>
                        </td>
                    </tr>
                </table>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" @click="updateTarget(bridge_index, target, index)"  data-dismiss="modal">Accept changes</button>
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
          </div>
        </div>
      </div>
    </div>`

var bridgeFormTmpl = `
<div class="modal" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit {{bridge.label}}</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body">
            <form>
                <table class="table" style="with:100%;">
                    <tr v-for="(v, k) in bridge" v-if="k !== 'targets'" class="form-group">
                        <td>{{k}}</td>
                        <td>
                            <input type="text" class="form-control" :id="'form-input-'+k" v-model="bridge[k]">
                        </td>
                        <td>
                            <button type="button" class="btn btn-sm btn-danger" @click="removeBridgeProp(index, k)">
                                X</button>
                        </td>
                    </tr>
                </table>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" @click="updateBridge(bridge, index)"  data-dismiss="modal">Accept changes</button>
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
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
            <strong>{{ key }}:</strong> {{ value }}
        </div>
    </td>
    <td></td>
    <td>
        <button type="button" class="btn btn-sm btn-primary" data-toggle="modal" :data-target="'#target-form-'+bridge_index+'-'+index">Edit</button>
        <button type="button" class="btn btn-sm btn-danger" @click="removeTarget(bridge_index, index)">X</button>
        <target-form v-bind:target="getDeepCopy(target)" v-bind:bridge_index="bridge_index" v-bind:index="index" :id="'target-form-'+bridge_index+'-'+index"></target-form>
    </td>
</tr>`

var bridgeTmpl = `
<tr class="bridge" v-bind:class="{ edited: edited}">
	<td><span class="badge badge-primary">{{ bridge.type}}</span></td>
	<td><strong>{{ bridge.label}}</strong></td>
	<td>
		<div v-for="(v, k) in displayProps(bridge)" v-if="k !== 'targets'">
			<strong>{{k }}:</strong> {{v}}
		</div>
	</td>
	<td>
		<div v-for="target in bridge.targets">
			<span class="badge badge-success">{{ target.type}}</span>
		</div>
	</td>
	<td>
        <button type="button" class="btn btn-sm btn-primary" data-toggle="modal" :data-target="'#bridge-form-'+index">Edit</button>
        <button type="button" class="btn btn-sm btn-danger" @click="removeBridge(index)">X</button>
        <!--button type="button" class="btn btn-sm btn-primary" data-toggle="collapse" :data-target="'.target-'+index">Targets</button-->
        <bridge-form v-bind:bridge="getDeepCopy(bridge)" v-bind:index="index" :id="'bridge-form-'+index"></bridge-form>
	</td>
</tr>
`

Vue.component('auth-form', {
    template: authFormTmpl,
    props: ["auth", "name"],
    methods: {
        updateAuth: function(auth, name) {
           this.$parent.edited = true;
           this.$parent.$parent.$options.methods.updateAuth(auth, name)
        }
    }
})


Vue.component('auth', {
    template: authTmpl,
    props: ["name", "auth", "index"],
    data: function () {
        return {
            edited: false
        }
    },
    methods: {
        getDeepCopy: getDeepCopy
    }
})

Vue.component('target-form', {
    template: targetFormTmpl,
    props: ["bridge_index", "target", "index"],
    methods: {
        updateTarget: function(bridge_index, target, index) {
           this.$parent.edited = true;
           this.$parent.$parent.$options.methods.updateTarget(bridge_index, target, index)
        },
        removeTargetProp: function(bridge_index, index, key) {
            this.$parent.edited = true;
            this.$parent.$parent.$options.methods.removeTargetProp(bridge_index, index, key)
        }
    }
})

Vue.component('bridge-form', {
    template: bridgeFormTmpl,
    props: ["bridge", "index"],
    methods: {
        updateBridge: function(bridge, index) {
            this.$parent.edited = true;
            this.$parent.$parent.$options.methods.updateBridge(bridge, index)
        },
        removeBridgeProp: function(index, key) {
            this.$parent.edited = true;
            this.$parent.$parent.$options.methods.removeBridgeProp(index, key)
        }
    }
})

Vue.component('target', {
    template: targetTmpl,
    props: ["bridge_index", "target", "index"],
    data: function () {
        return {
            edited: false
        }
    },
    methods: {
        displayProps: displayProps,
        getDeepCopy: getDeepCopy,
        removeTarget: function(bridge_index, index) {
           this.$parent.$options.methods.removeTarget(bridge_index, index)
        }

    }
})

Vue.component('bridge', {
    template: bridgeTmpl,
    props: ["bridge", "index"],
    data: function () {
        return {
            edited: false
        }
    },
    methods: {
        displayProps: displayProps,
        getDeepCopy: getDeepCopy,
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
        edited: false
    },
    mounted() {
        this.getControlData()
    },
    methods: {
        getDeepCopy: getDeepCopy,
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
        updateBridge: function(bridge, index) {
           app.control_data.bridges.splice(index, 1, bridge)
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
        removeTarget: function(bridge_index, index) {
            app.control_data.bridges[bridge_index].targets.splice(index, 1)
            app.edited = true
        },
        removeTargetProp: function(bridge_index, index, key) {
            Vue.delete(app.control_data.bridges[bridge_index].targets[index], key)
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
    },
    computed: {
   }
})

