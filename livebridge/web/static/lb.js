var lbMixin = {
    data: function() {
        return {
            typeHint: false,
            labelHint: false
        }
    },
    methods: {
        linkify: function (value) {
            if (!value) return ''
            value = value.toString()
            if(value.startsWith("http"))
                return '<a href="'+value+'" target="_blank">'+value+'</a>'
            return value;
        },
        displayProps: function (data, mode) {
            var props = {};
            var filterProps = ["type", "label", "__edited"]

            if(mode === "auth")
                filterProps = ["__edited"]

            for(var prop in data) {
                if(filterProps.indexOf(prop) == -1 ) {
                    props[prop] = data[prop]
                }
            }
            return props;
        },
        getDeepCopy: function(data) {
            return JSON.parse(JSON.stringify(data))
        },
        valueChoices: function(propName) {
            return (app !== undefined) ? Array.from(new Set(app.valueChoices[propName])).sort() : [];
        },
        keyChoices: function(propName) {
            return (app !== undefined) ? app.keyChoices : [];
        },
        validateNode: function(node) {
            this.resetHints()
            if(node.label === "")
                this.labelHint = true

            if(node.type === "")
                this.typeHint = true

            if (node.type === undefined) {
                app.showMessage("A 'type' has to be specified!", "danger");
            } else {
                return (this.typeHint || this.labelHint) ?  false : true;
            }
        },
        resetHints: function() {
            this.typeHint = false;
            this.labelHint = false;
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
                    <table class="table">
                        <tr v-for="(v, k) in local_auth" v-if="['__edited'].indexOf(k) < 0" class="form-group">
                            <td>{{k}}</td>
                            <td>
                                <input type="text" class="form-control" :id="'form-input-'+k" v-model="local_auth[k]"></td>
                            <td>
                                <button type="button" class="btn btn-sm btn-danger" @click="removeAuthProp(k)">
                                    X</button>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <input type="text" v-model="add_key" class="form-control" placeholder="Property name" list="authlist">
                                <datalist id="authlist">
                                    <option v-for="val in keyChoices()" :value="val"/>
                                </datalist>
                            </td>
                            <td>
                                <input type="text" v-model="add_value" class="form-control" placeholder="Property value" list="auth_vals">
                                <datalist id="auth_vals" v-if="add_key !== ''">
                                    <option v-for="val in valueChoices(add_key)" :value="val"/>
                                </datalist>
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
<div v-bind:class="{ edited: auth.__edited}" class="auth rounded">
    <div class="card">
        <div class="card-header">
            <h4>{{ name }}</h4>
            <div class="float-right">
                <button type="button" class="btn btn-sm btn-primary" data-toggle="modal" :data-target="'#auth-form-'+index"
                    title="Edit account">Edit</button>
                <button type="button" class="btn btn-sm btn-danger" @click="removeAuth(name)" title="Remove account">&Chi;</button>
            </div>
        </div>
        <div class="card-body">
            <div class="card-text">
                <div v-for="(v, k) in displayProps(auth, 'auth')">
                    <strong>{{ k }}:</strong>  <span v-html="linkify(v)"></span>
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
                <table class="table">
                    <tr v-for="(v, k) in local_target" v-if="['__edited'].indexOf(k) < 0" class="form-group">
                        <td>{{k}}</td>
                        <td>
                            <input type="text" class="form-control" v-bind:class="{ 'is-invalid': ((k==='type' && typeHint) || (k==='label' && labelHint))}" :id="'form-input-'+k" v-model="local_target[k]" :list="k+'-'+index">
                            <datalist :id="k+'-'+index">
                                <option v-for="val in valueChoices(k)" :value="val"/>
                            </datalist>
                        </td>
                        <td>
                            <button type="button" class="btn btn-sm btn-danger" @click="removeTargetProp(k)">
                                X</button>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="text" v-model="add_key" class="form-control" placeholder="Property name" :list="'_keylist'+index">
                            <datalist :id="'_keylist'+index">
                                <option v-for="val in keyChoices()" :value="val"/>
                            </datalist>
                        </td>
                        <td>
                            <input type="text" v-model="add_value" class="form-control" placeholder="Property value" list="target_vals">
                            <datalist id="target_vals" v-if="add_key !== ''">
                                <option v-for="val in valueChoices(add_key)" :value="val"/>
                            </datalist>
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
            <button v-if="index < 0" type="button" class="btn btn-primary" @click="addTarget($event)" data-dismiss="modal">Add new target</button>
            <button v-else type="button" class="btn btn-primary" @click="updateTarget($event)"  data-dismiss="modal">Accept changes</button>
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
                <table class="table">
                    <tr v-for="(v, k) in local_bridge" v-if="['targets', '__edited'].indexOf(k) < 0" class="form-group">
                        <td>{{k}}</td>
                        <td>
                            <input type="text" class="form-control"  v-bind:class="{ 'is-invalid': ((k==='type' && typeHint) || (k==='label' && labelHint))}" :id="'form-input-'+k" v-model="local_bridge[k]" :list="k">
                            <datalist :id="k">
                                <option v-for="val in valueChoices(k)" :value="val"/>
                            </datalist>
                        </td>
                        <td>
                            <button type="button" class="btn btn-sm btn-danger" @click="removeBridgeProp(k)">
                                X</button>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="text" v-model="add_key" class="form-control" placeholder="Property name" list="key">
                            <datalist id="key">
                                <option v-for="val in keyChoices()" :value="val"/>
                            </datalist>
                        </td>
                        <td>
                            <input type="text" v-model="add_value" class="form-control" placeholder="Property value" list="vals">
                            <datalist id="vals" v-if="add_key !== ''">
                                <option v-for="val in valueChoices(add_key)" :value="val"/>
                            </datalist>
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
            <button v-if="index < 0" type="button" class="btn btn-primary" @click="addBridge($event)" data-dismiss="modal">
               Create new bridge</button>
            <button v-else type="button" class="btn btn-primary" @click="updateBridge($event)"  data-dismiss="modal">Accept changes</button>
            <button type="button" class="btn btn-secondary" @click="reset()" data-dismiss="modal">Cancel</button>
          </div>
        </div>
      </div>
    </div>`

var targetTmpl = `
<tr class="target" v-bind:class="{edited: target.__edited}">
    <td><span class="badge badge-success align-middle">{{ target.type }}</span></td>
    <td>
    	<strong>{{ target.label }}</strong></td>
    <td>
        <div v-for="(value, key) in displayProps(target)">
            <strong>{{ key }}:</strong>  <span v-html="linkify(value)"></span>
        </div>
    </td>
    <td class="target-actions">
        <button type="button" class="btn btn-sm btn-primary justify-content-end" title="Edit target" data-toggle="modal"
            :data-target="'#target-form-'+bridge_index+'-'+index">Edit</button>
        <button type="button" class="btn btn-sm btn-danger" @click="removeTarget(bridge_index, index)" title="Remove target">&Chi;</button>
        <target-form v-bind:target="getDeepCopy(target)" v-bind:bridge="bridge" v-bind:bridge_index="bridge_index" v-bind:index="index" :id="'target-form-'+bridge_index+'-'+index"></target-form>
    </td>
</tr>`


var bridgeTmpl = `
<div v-bind:class="{ edited: bridge.__edited}" class="bridge rounded">
    <div class="card source">
        <div class="card-header">
            <h4>
                <span class="badge badge-primary">{{ bridge.type}}</span>
                {{ bridge.label }}
            </h4>
            <div class="float-right">
                <button type="button" class="btn btn-sm btn-primary" data-toggle="modal" :data-target="'#bridge-form-'+index"
                    title="Edit source">Edit</button>
                <button type="button" class="btn btn-sm btn-success" data-toggle="modal" :data-target="'#target-add-form-'+index"
                    title="Add target">&plus;</button>
                <button type="button" class="btn btn-sm btn-danger" @click="removeBridge(index)" title="Remove bridge">&Chi;</button>
            </div>
        </div>
        <div class="card-body">
            <bridge-form v-bind:bridge="getDeepCopy(bridge)" v-bind:index="index" :id="'bridge-form-'+index"></bridge-form>
            <target-form v-bind:bridge_index="index" v-bind:bridge="bridge" v-bind:index="-1" :id="'target-add-form-'+index"></target-form>
            <!--h4 class="card-title"-->
            <div class="card-text">
                <div v-for="(v, k) in displayProps(bridge)" v-if="k !== 'targets'">
                    <strong>{{k }}:</strong> <span v-html="linkify(v)"></span>
                </div>
            </div>
            <table class="table table-bordered table-sm targets rounded">
                <tr is="target" v-for="(target, x) in bridge.targets" v-bind:bridge_index="index" v-bind:bridge="bridge"
                        v-bind:target="target" v-bind:index="x" :id="'target-'+index" :key="'target-'+index+'-'+x" >
                </tr>
            </table>
        </div>
    </div>
</div>`

var flashMessageTmpl = `
<transition name="fade">
    <div :class="'alert alert-'+message.mode" class="flash-msg text-center fixed-top" role="alert" v-if="message.flash">
        <button type="button" class="close" aria-label="Close" @click="message.flash=false;">
            <span aria-hidden="true">&times;</span>
        </button>
        <h5 class="alert-heading">{{ message.txt }}</h5>
    </div>
</transition>
`


Vue.component('auth-form', {
    template: authFormTmpl,
    props: ["auth", "name", "mode"],
    mixins: [lbMixin],
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
    mixins: [lbMixin],
    data: function () {
        return {
            local_target: (this.index < 0) ? {"type": "", "label": ""} : this.target,
            add_key: "",
            add_value: ""
        }
    },
    methods: {
        addTarget: function(ev) {
            if(this.validateNode(this.local_target)) {
                this.$parent.$parent.$options.methods.addTarget(this.bridge_index, this.local_target)
                this.$parent.edited = true;
                this.reset()
            } else {
                ev.preventDefault();
                ev.stopPropagation();
            }
        },
        updateTarget: function(ev) {
            if(this.validateNode(this.local_target)) {
                this.$parent.edited = true;
                this.$parent.$parent.$parent.$options.methods.updateTarget(this.bridge_index, this.local_target, this.index)
            } else {
                ev.preventDefault();
                ev.stopPropagation();
            }
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
    mixins: [lbMixin],
    data: function () {
        return {
            local_bridge: (this.index < 0) ? {"type": "", "label": ""} : this.bridge,
            add_key: "",
            add_value: ""
        }
    },
    methods: {
        addBridge: function(ev) {
            if(this.validateNode(this.local_bridge)) {
                this.$parent.$options.methods.addBridge(this.local_bridge)
                this.reset()
            } else {
                ev.preventDefault();
                ev.stopPropagation();
            }
        },
        updateBridge: function(ev) {
            if(this.validateNode(this.local_bridge)) {
                this.$parent.$parent.$options.methods.updateBridge(this.local_bridge, this.index)
                this.$parent.edited = true;
            } else {
                ev.preventDefault();
                ev.stopPropagation();
            }
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
           this.$parent.$parent.$options.methods.removeTarget(bridge_index, index)
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

Vue.component('flash-message', {
    template: flashMessageTmpl,
    props: ["message"]
})

var app = new Vue({
    el: '#content',
    data: {
        cookie_name: "lb-db",
        etag: "",
        loginUser: null,
        loginPassword: null,
        loggedIn: true,
        control_data: {},
        control_data_orig: {},
        username: null,
        password: null,
        edited: false,
        new_auth_key: '',
        json_str: '',
        keyChoices: [],
        valueChoices: {},
        message: {
            txt: "",
            mode: "",
            flash: false
        }
    },
    mounted() {
        this.getControlData()
    },
    methods: {
        showMessage: function(txt, mode) {
            this.message.txt = txt
            this.message.mode = mode
            this.message.flash = true
            if(mode === "success")
                setTimeout(function(){ app.message.flash = false; }, 3000);
        },
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
                    console.info(error);
                    app.showMessage("Login failed, please check your credentials!", "danger");
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
        clearObject: function(key, obj, depth) {
            var d = (key) ? (depth +1): depth
            if((typeof obj) == "object") {
                delete obj["__edited"]
                for(var prop in obj) {
                    var val = obj[prop]
                    this.clearObject(prop, val, d)
                }
            }
        },
        addChoice: function(prop, value) {
            if(this.keyChoices.indexOf(prop) < 0)
                this.keyChoices.push(prop);

            if(this.valueChoices[prop] === undefined)
                this.valueChoices[prop] = [value];
            else this.valueChoices[prop].push(value);
        },
        collectChoices: function(key, obj, depth) {
            var d = (key) ? (depth +1): depth
            if((typeof obj) == "object") {
                for(var prop in obj) {
                    var val = obj[prop]
                    if(typeof(val) === "string")
                        this.addChoice(prop, val)
                    this.collectChoices(prop, val, d)
                }
            }
        },
        getControlData: function() {
            var cookie_token = this.getCookie();
            axios({
                method: 'get',
                url: '/api/v1/controldata'
            }).then(response => {
                this.etag = response.headers.etag
                this.control_data = response.data;
                this.control_data_orig = JSON.parse(JSON.stringify(response.data));
                this.collectChoices("", this.control_data, -1)
                this.keyChoices.sort()
                //this.printObject("", this.control_data, -1);
            }).catch(error =>  {
                if(error)
                    console.debug(error);
                if(error.response && error.response.status === 401) {
                    this.loggedIn = false;
                    this.login()
                }
            });
        },
        checkNewAuthName: function(name, e) {
            var skip = false;
            name = name.trim();
            if(name === "") {
                this.showMessage("Please specify an account name!", "danger");
                skip = true;
            } else if(this.control_data.auth[name] !== undefined) {
                this.showMessage("Account name already exists!", "danger");
                skip = true;
            }
            if(skip === true) {
                e.preventDefault();
                e.stopPropagation();
           }
        },
        addAuth: function(new_key, new_auth) {
            app.collectChoices("", {new_key: new_auth}, -1)
            new_auth["__edited"] = true;
            app.$set(app.control_data.auth, new_key, new_auth)
            app.new_auth_key = ""
            app.edited = true
        },
        updateAuth: function(auth, name) {
            app.collectChoices("", {name: auth}, -1)
            auth["__edited"] = true;
            app.$set(app.control_data.auth, name, auth)
            app.edited = true
        },
        removeAuth: function(name) {
            Vue.delete(app.control_data.auth, name)
            app.edited = true
        },
        addBridge: function(new_bridge) {
            app.collectChoices("", new_bridge, -1)
            new_bridge["targets"] = [];
            new_bridge.__edited = true;
            app.control_data.bridges.unshift(new_bridge)
            app.edited = true
        },
        updateBridge: function(bridge, index) {
            app.collectChoices("", bridge, -1)
            bridge.__edited = true
            app.control_data.bridges.splice(index, 1, bridge)
            app.edited = true
        },
        removeBridge: function(index) {
            app.control_data.bridges.splice(index, 1)
            app.edited = true
        },
        addTarget: function(bridge_index, target) {
            app.collectChoices("", target, -1)
            target["__edited"] = true
            var data = JSON.parse(JSON.stringify(app.control_data));
            data.bridges[bridge_index].targets.push(target)
            app.control_data = data
            app.edited = true
        },
        updateTarget: function(bridge_index, target, index) {
            app.collectChoices("", target, -1)
            target["__edited"] = true
            app.control_data.bridges[bridge_index].targets.splice(index, 1, target)
            app.edited = true
        },
        removeTarget: function(bridge_index, index) {
            app.control_data.bridges[bridge_index].targets.splice(index, 1)
            app.control_data.bridges[bridge_index].__edited = true
            app.edited = true
        },
        fillJSONForm: function(ev) {
            if(confirm("Your changes are going to be lost, you're entering expert mode. Ok?")) {
                this.undoChanges();
                this.json_str = JSON.stringify(this.control_data_orig, null, 4);
                return true;
            }
            ev.preventDefault();
            ev.stopPropagation();
            return false;
        },
        saveJSON: function() {
            var newData = null;
            try {
                newData = JSON.parse(this.json_str);
                this.control_data = newData;
                this.saveNewControlData();
                return true;
            } catch(err) {
                app.showMessage(err.message, "danger")
            }
            return false;
        },
        undoChanges: function() {
            this.control_data = JSON.parse(JSON.stringify(this.control_data_orig));
            app.edited = false
        },
        saveNewControlData: function() {
            app.edited = false
            var payload = JSON.parse(JSON.stringify(this.control_data));
            this.clearObject("", payload, -1)
            axios({
                method: 'put',
                url: '/api/v1/controldata',
                data: payload,
                headers: {
                    "X-Auth-Token": app.token,
                    "If-Match": app.etag
                }
            })
            .then(response => {
                this.showMessage("Data was successfully saved!", "success");
                this.getControlData()
            }).catch(function (error) {
                if(error.reponse)
                    console.debug(error.response.status);
                app.showMessage(error.response.data.error, "danger");
            });
        }
    }
})

