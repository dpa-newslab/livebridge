var displayProps = function (data) {
    var props = {};
    for(var prop in data) {
        if(["type", "label"].indexOf(prop) == -1 ) {
            props[prop] = data[prop]
        }
    }
    return props;
}

var bridgeFormTmpl = `
<div class="modal" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit {{bridge.label}} {{index}}</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body">
            <form>
                <table class="table" style="with:100%;">
                    <tr v-for="(v, k) in bridge" v-if="k !== 'targets'" class="form-group">
                        <td>{{k}}</td>
                        <td><input type="text" class="form-control" :id="'form-input-'+k" v-model="bridge[k]"></td>
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
<ul>
    <li class="list-group-item"><span class="badge badge-success">{{ target.type}}</span></li>
    <li v-for="(value, key) in displayProps(target)" class="target-prop list-group-item">
        {{ key }}: {{ value }}
    </li>
</ul>`

var bridgeTmpl = `
<div v-bind:class="{ edited: edited}">
    <div class="card source">
        <h4 class="card-header">
                    <span class="badge badge-primary">{{ bridge.type}}</span>
                    {{ bridge.label }}
                    <button type="button" class="btn btn-primary" data-toggle="modal" :data-target="'#bridge-form-'+index">Edit</button>
        </h4>
        <div class="card-body">
            <!--h4 class="card-title"-->
            <div class="card-text">
                <div v-for="(v, k) in displayProps(bridge)" v-if="k !== 'targets'">
                    {{k }}: {{v}}
                </div>
            </div>
            <div>
                <span v-for="target in bridge.targets" class="badge badge-success">
                    {{ target.type}}
                </span>
            </div>
            <a href="#" class="btn-sm btn-primary" data-toggle="collapse" :data-target="'#targets-'+index" aria-expanded="false" :aria-controls="'#targets-'+index">Show targets</a>
            <div class="targets collapse" :id="'targets-'+index">
                <ul is="target" v-for="target in bridge.targets" v-bind:target="target" class="target list-group" />
            </div>
        </div>
    </div>
    <bridge-form v-bind:bridge="getDeepCopy(bridge)" v-bind:index="index" :id="'bridge-form-'+index"></bridge-form>
</div>`

Vue.component('bridge-form', {
    template: bridgeFormTmpl,
    props: ["bridge", "index"],
    methods: {
        updateBridge: function(bridge, index) {
           this.$parent.edited = true;
           this.$parent.$parent.$options.methods.updateBridge(bridge, index)
        }
    }
})

Vue.component('target', {
    template: targetTmpl,
    props: ["target"],
    methods: {
	    displayProps: displayProps
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
        getDeepCopy: function(data) {
            return JSON.parse(JSON.stringify(data))
        }
    }
})


var app = new Vue({
	el: '#content',
	data: {
		token: null,
		control_data: {},
		control_data_orig: {},
		username: "admin",
		password: "admin",
        edited: false
	},
	mounted() {
		this.checkToken()
	},
	methods: {
		checkToken: function() {
			if (!this.token) {
				axios({
				  method: 'post',
				  url: '/api/v1/session',
				  data: "username=admin&password=admin"
				})
				.then(function (response) {
					app.token = response.data.token;
					this.app.getControlData(app.token);
				})
				.catch(function (error) {
					console.log(error);
				});
			}
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
		getControlData: function(token) {
			axios({
				method: 'get',
				url: '/api/v1/controldata',
				data: "username=admin&password=admin",
				headers: {
				"X-Auth-Token": token
				}
			})
			.then(response => {
				this.control_data = response.data;
				this.control_data_orig = JSON.parse(JSON.stringify(response.data));
				//this.printObject("", this.control_data, -1);
			}).catch(function (error) {
				if(error.reponse)
					console.debug(error.response.status);
				console.log(error.message);
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

