var mypapers = [];
var myfavouritepapers = [];

var previously_selected_rooms_render = [];
var selected_rooms = [];
var current_adjacency_department = [];
var room_selection_papers = [];
var current_group = [];
var specified_rooms = [];

var render_array = [];
var group_id = 0;
var groups = [];
var edges_of_groups = [];

var favourites = [];
var favourite_id = 0;

// setup canvases
$(document).ready(
	setup_canvases
);

$(document).ready(
	get_floorplans('restart', [], [])
);

function setup_canvases(){
	var canvases = jQuery.makeArray($(".floor_canvas"));
	canvases.forEach(function(element){
		var newpaper = new paper.PaperScope();
		newpaper.setup(element);
		mypapers.push(newpaper);
	});
};

function setup_favourite_canvases(){
	var favourite_canvases = jQuery.makeArray($(".favourite_plan"));
	myfavouritepapers = [];
	favourite_canvases.forEach(function(element){
		var newpaper = new paper.PaperScope();
		newpaper.setup(element);
		myfavouritepapers.push(newpaper);
	});
};


function get_floorplans(mode, user_groups, edges_of_user_groups){
	$.post('/get_floorplans',{
		mode: mode,
		user_groups: JSON.stringify(user_groups),
		edges_of_user_groups: JSON.stringify(edges_of_user_groups)
	}).done(function(response) {
		render_array = response;
		render_floorplans(render_array);
	});
};

// button onclick handlers
$("#generate_button").click(function(){
	var mode = 'new';
	get_floorplans(mode, groups, edges_of_groups);
	console.log("groups", groups);
});

function change_transit_of_department(group,department) {
	$.post('/change_transit_of_department',{
		department: department
	}).done(function(response) {
		var index =	group.rooms.findIndex(function(room) {
			return (room.name == department)
		});
		group.rooms[index].transit = response;
		if (response == 0){
			var border = 1
		}else{
			var border = 3
		}
		node_dict = {id: department, label: department, group: group.name, borderWidth: border};
		group.nodes[index] = node_dict
		update_network(group);
	});
};

function update_group(group_name,room){
	var gr_index = groups.findIndex(function(gr) {
		return (gr.name == group_name)
	});
	var rm_index = groups[gr_index].rooms.findIndex(function(rm) {
		return (rm.name == room.name)
	});
	if(rm_index>-1){
		groups[gr_index].rooms.splice(rm_index,1);
	} else {
		groups[gr_index].rooms.push(room);
	};
	groups[gr_index].nodes = [];
	groups[gr_index].rooms.forEach(function(room){
		// if it is a transit element, add a thick border
		if (room.transit == 0){
			var border = 1
		}else{
			var border = 3
		}
		node_dict = {id: room.name, label: room.name, group: groups[gr_index].name, borderWidth: border};
		groups[gr_index].nodes.push(node_dict);
});
};

$("#select_group_button").click(function(){
	group_name = document.getElementById("select_group").value;
	console.log(group_name);
	current_group.forEach(function(room){
		update_group(group_name,room)
	});
	update_groups_for_network(groups);
	update_group_network(groups,edges_of_groups);
	var index =	groups.findIndex(function(group) {
		return (group.name == group_name)
	});

	update_network(groups[index]);
	render_floorplans(render_array);
	current_group = [];
});

$("#add_favourite_button").click(function(){
	console.log("clicked")
	add_favourite_card(favourite_id);
	favourites.push(render_array[0]);
	setup_favourite_canvases()
	render_favourites(favourites);
	favourite_id ++;
});

function add_favourite_card(favourite_id) {
	// create a new div element
	var newRow = document.createElement("div");
	newRow.setAttribute('class', 'row');
	newRow.setAttribute('name', favourite_id);
	var newCol = document.createElement("div");
	newCol.setAttribute('class', 'col-md-12');
	var newCard = document.createElement("div");
	newCard.setAttribute('class', 'card');
	var newCardBody = document.createElement("div");
	newCardBody.setAttribute('class', 'card-body');
	var newCanvas = document.createElement("canvas");

	newCanvas.setAttribute('class', 'favourite_plan');
	newCanvas.setAttribute('id', favourite_id);
	newCanvas.setAttribute('width', 300);
	newCanvas.setAttribute('height', 100);

	newCardBody.appendChild(newCanvas);
	newCard.appendChild(newCardBody);
	newCol.appendChild(newCard);
	newRow.appendChild(newCol);

	var fav_location = document.getElementById('favourites');
	var paragraph = document.createElement("p");
	fav_location.insertBefore(paragraph, fav_location.childNodes[0])
	fav_location.insertBefore(newRow, fav_location.childNodes[0])
};


$("#add_group_button").click(function(){
	// get name from field and delete it
	group_name = document.getElementById("name_of_group").value;
	document.getElementById("name_of_group").value = "";
	// add a card for the group
	add_group_card(group_name);
	group_dict = {name:group_name, rooms:current_group};
	init_group_adjacents(group_dict);
	groups.push(group_dict);

	current_group.forEach(function(element){
		specified_rooms.push({name:element.name, group:group_name});
	});

	update_groups_for_network(groups);
	update_group_network(groups,edges_of_groups);
	// find index of element in groups array
	var index =	groups.findIndex(function(group) {
		return (group.name == group_name)
	});

	// pass that array to the opdate network function
	update_network(groups[index]);
	render_floorplans(render_array);
	update_group_selections();
	current_group = [];
});

function update_group_selections() {
	var select_group = document.getElementById("select_group");
	while (select_group.firstChild) {
		select_group.removeChild(select_group.firstChild);
	}
	groups.forEach(function(group){
		var group_option = document.createElement("option");
		group_option.innerHTML = group.name;
		select_group.appendChild(group_option);
	});
}

function add_group_card(group_name) {
	// create a new div element
	var newRow = document.createElement("div");
	newRow.setAttribute('class', 'row');
	newRow.setAttribute('name', group_name);
	var newCol = document.createElement("div");
	newCol.setAttribute('class', 'col-md-12');
	var newCard = document.createElement("div");
	newCard.setAttribute('class', 'card');
	var newCardBody = document.createElement("div");
	newCardBody.setAttribute('class', 'card-body');
	var newNetwork = document.createElement("div");
	newNetwork.setAttribute('class', 'subnetwork');
	newNetwork.setAttribute('id', group_name);
	var newTitle = document.createElement("h5");
	newTitle.setAttribute('class', 'card-title');
	newTitle.innerHTML = group_name;

	newCardBody.appendChild(newTitle);
	newCardBody.appendChild(newNetwork);
	newCard.appendChild(newCardBody);
	newCol.appendChild(newCard);
	newRow.appendChild(newCol);

	var group_location = document.getElementById('groups');
	var paragraph = document.createElement("p");
	group_location.insertBefore(paragraph, group_location.childNodes[0])
	group_location.insertBefore(newRow, group_location.childNodes[0])
};


function init_group_adjacents(group){
	group.edges = [];
	group.nodes = [];
	group.rooms.forEach(function(room){
		// if it is a transit element, add a thick border
		if (room.transit == 0){
			var border = 1
		}else{
			var border = 3
		}
		node_dict = {id: room.name, label: room.name, group: group.name, borderWidth: border};
		group.nodes.push(node_dict);
		compare_and_add(group,room);
	});
};

function compare_and_add(group,element) {
	var adajcent_rooms = render_array[element.render_id].all_adjacency_dict[element.name];
	group.rooms.forEach(function(room){
		adajcent_rooms.forEach(function(adj_room){
			if (room.name == adj_room){
				var index =	group.edges.findIndex(function(el) {
					return (el.to == room.name && el.from == element.name ||
						el.to == element.name && el.from == room.name)
					});
					if (index == -1){
						edge_dict = {};
						edge_dict.from = element.name;
						edge_dict.to = room.name;
						group.edges.push(edge_dict);
				};
			};
		});
	});
};

function render_favourites(favourites) {
	favourite_canvases = jQuery.makeArray($(".favourite_plan"));
	for( var i = 0; i< favourite_canvases.length; i++){
		plotPlan(favourite_canvases[i],i,favourites[i]);
	};
};

function render_floorplans(render_array) {
	canvases = jQuery.makeArray($(".floor_canvas"));
	for( var i = 0; i< canvases.length; i++){
		plotPlan(canvases[i],i,render_array[i]);
		canvases[i].setAttribute('plan_id',render_array[i].id);
	};
};

function parse_dim(float) {
		return parseFloat(Math.round(float * 100) / 100).toFixed(0);
};

function plotPlan(plotCanvas,project_id,render_graphics) {
		mypapers[project_id].activate();
		mypapers[project_id].view.draw();
		var layer = new Layer();
		mypapers[project_id].project.clear()
		mypapers[project_id].project.addLayer(layer)
		var render_id = render_graphics.id;

		max_size = render_graphics.max_sizes;
		var factor_x = parseInt(plotCanvas.style.width) / max_size[1];
		var factor_y = parseInt(plotCanvas.style.height) / max_size[0];
		var scale_factor = Math.min(factor_x,factor_y);

		// outline for the floor plan

		var base = new Point(0,0);
		var dims = new Size(max_size[1]*scale_factor,max_size[0]*scale_factor)

		var departments = render_graphics.departments;
		var walls = render_graphics.walls;

		departments.forEach(function(element) {
			var base = new Point(element.base[0]*scale_factor,element.base[1]*scale_factor);
			var dims = new Size(element.dims[1]*scale_factor,element.dims[0]*scale_factor);
			var name = element.name;
			var department = new Rectangle(base,dims);
			var path = new Path.Rectangle(department);
			var fillColor = 'lightgrey'

			// loop through groups
			groups:
			for (i = 0; i < groups.length; i++) {
				group_name = groups[i].name;
				// loop through rooms of group members
				for (n = 0; n < groups[i].rooms.length; n++) {
					// if the name of the room is the same, break
					if (groups[i].rooms[n].name == name) {
						fillColor = options.groups[group_name].color.background;
						break groups;
					};
				};
			};

			path.fillColor = fillColor;
			path.name = name;
			path.selected = false;
			path.opacity = 0.5;

			var font_size = 12;
			var center_point = new Point(department.center._x,department.center._y);
			var text_name = new PointText(center_point);
			text_name.fillColor = 'black';
			text_name.fontSize = font_size;
			text_name.justification = 'center';
			text_name.content = name.replace(/[0-9]/g, '');

			var type_point = new Point(department.center._x,department.center._y+font_size);
			var text_type = new PointText(type_point);
			text_type.fillColor = 'grey';
			text_type.fontSize = font_size;
			text_type.fontWeight = 'italic'
			text_type.justification = 'center';
			text_type.content = parse_dim(element.dims[1]*element.dims[0]).concat(" m2");

			// mouseevents
			path.onMouseEnter = function(event) {
				this.fillColor = 'lightgreen';
			};

			path.onClick = function(event) {
				var index =	current_group.findIndex(function(element) {
					return (element.name == name);
				});
				if (index > -1){
					current_group.splice(index,1);
					this.fillColor = 'lightgrey';
				} else {
					var department_dict = {};
					department_dict.name = element.name;
					department_dict.plan_id = render_id;
					department_dict.render_id = project_id;
					department_dict.transit = element.transit;
					current_group.push(department_dict);
					this.fillColor = 'green';
				};
			};

			path.onMouseLeave = function(event) {
				var index =	current_group.findIndex(function(element) {
					return (element.name == name);
				});
				// if it is in the group
				if (index > -1){
					this.fillColor = 'green';
				} else {
					this.fillColor = fillColor;
				};
			};
		});

		walls.forEach(function(element) {
			var from = new Point(element[0][0]*scale_factor,element[0][1]*scale_factor)
			var to  = new Point(element[1][0]*scale_factor,element[1][1]*scale_factor)
			var path = new Path.Line(from, to);
			path.strokeColor = 'black';
			path.strokeWidth = 1;
		});

		var outlineWidth = 5;
		var outline = new Rectangle(base,dims);
		var path = new Path.Rectangle(outline);
		path.strokeColor = 'black';
		path.strokeWidth = outlineWidth;
		var onpath = new Path.Rectangle(outline);
		onpath.strokeColor = 'white';
		onpath.strokeWidth = outlineWidth-2;
	};

	function plotFavorites(plotCanvas,project_id,render_graphics) {
			mypapers[project_id].activate();
			mypapers[project_id].view.draw();
			var layer = new Layer();
			mypapers[project_id].project.clear()
			mypapers[project_id].project.addLayer(layer)
			var render_id = render_graphics.id;

			max_size = render_graphics.max_sizes;
			var factor_x = parseInt(plotCanvas.style.width) / max_size[1];
			var factor_y = parseInt(plotCanvas.style.height) / max_size[0];
			var scale_factor = Math.min(factor_x,factor_y);

			// outline for the floor plan

			var base = new Point(0,0);
			var dims = new Size(max_size[1]*scale_factor,max_size[0]*scale_factor)

			var departments = render_graphics.departments;
			var walls = render_graphics.walls;

			departments.forEach(function(element) {
				var base = new Point(element.base[0]*scale_factor,element.base[1]*scale_factor);
				var dims = new Size(element.dims[1]*scale_factor,element.dims[0]*scale_factor);
				var name = element.name;
				var department = new Rectangle(base,dims);
				var path = new Path.Rectangle(department);
				var fillColor = 'lightgrey'

				// loop through groups
				groups:
				for (i = 0; i < groups.length; i++) {
					group_name = groups[i].name;
					// loop through rooms of group members
					for (n = 0; n < groups[i].rooms.length; n++) {
						// if the name of the room is the same, break
						if (groups[i].rooms[n].name == name) {
							fillColor = options.groups[group_name].color.background;
							break groups;
						};
					};
				};

				path.fillColor = fillColor;
				path.name = name;
				path.selected = false;
				path.opacity = 0.5;

				var font_size = 12;
				var center_point = new Point(department.center._x,department.center._y);
				var text_name = new PointText(center_point);
				text_name.fillColor = 'black';
				text_name.fontSize = font_size;
				text_name.justification = 'center';
				text_name.content = name.replace(/[0-9]/g, '');

				var type_point = new Point(department.center._x,department.center._y+font_size);
				var text_type = new PointText(type_point);
				text_type.fillColor = 'grey';
				text_type.fontSize = font_size;
				text_type.fontWeight = 'italic'
				text_type.justification = 'center';
				text_type.content = parse_dim(element.dims[1]*element.dims[0]).concat(" m2");

				// mouseevents
				path.onMouseEnter = function(event) {
					this.fillColor = 'lightgreen';
				};

				path.onClick = function(event) {
					var index =	current_group.findIndex(function(element) {
						return (element.name == name);
					});
					if (index > -1){
						current_group.splice(index,1);
						this.fillColor = 'lightgrey';
					} else {
						var department_dict = {};
						department_dict.name = element.name;
						department_dict.plan_id = render_id;
						department_dict.render_id = project_id;
						department_dict.transit = element.transit;
						current_group.push(department_dict);
						this.fillColor = 'green';
					};
				};

				path.onMouseLeave = function(event) {
					var index =	current_group.findIndex(function(element) {
						return (element.name == name);
					});
					// if it is in the group
					if (index > -1){
						this.fillColor = 'green';
					} else {
						this.fillColor = fillColor;
					};
				};
			});

			walls.forEach(function(element) {
				var from = new Point(element[0][0]*scale_factor,element[0][1]*scale_factor)
				var to  = new Point(element[1][0]*scale_factor,element[1][1]*scale_factor)
				var path = new Path.Line(from, to);
				path.strokeColor = 'black';
				path.strokeWidth = 1;
			});

			var outlineWidth = 5;
			var outline = new Rectangle(base,dims);
			var path = new Path.Rectangle(outline);
			path.strokeColor = 'black';
			path.strokeWidth = outlineWidth;
			var onpath = new Path.Rectangle(outline);
			onpath.strokeColor = 'white';
			onpath.strokeWidth = outlineWidth-2;
		};






	// network script
	var options = {
		"nodes": {
			"shape": "dot"
		},
		"edges": {
			"smooth": {
				"forceDirection": "none"
			}
		},
		"interaction": {
			"dragNodes": false,
			"dragView": false,

			"selectConnectedEdges": false,
			"hoverConnectedEdges": false,
			"zoomView": false
		},
		"physics": {
			"forceAtlas2Based": {
				"gravitationalConstant": -20,
				"springLength": 10,
				"springConstant": 0.05,
				"avoidOverlap": 1
			},
			"minVelocity": 0.75,
			"solver": "forceAtlas2Based",
			"timestep": 1
		}
	}

	function update_groups_for_network(groups){
		options.groups = {};
		var colors = ['LightSeaGreen','LightBlue','LightSkyBlue','LightSteelBlue','LightCoral','LightCyan']
		groups.forEach(function(group) {
			options.groups[group.name] = {
				color: {background:colors[0],border:"black"}
			};
			colors.splice(0,1);
		});
	}

	function update_network(group){
		var adding = false;
		var from_node = 0;
		var to_node = 0;
		var data = {
			nodes: group.nodes,
			edges: group.edges
		};
		var container = document.getElementById(group.name);
		var network = new vis.Network(container, data, options);

		network.on("selectEdge", function (params) {
			var index =	group.edges.findIndex(function(edge) {
				return (edge.id == params.edges[0]);
			});
			group.edges.splice(index,1);
			update_network(group);
		});

		network.on("doubleClick", function (params) {
			change_transit_of_department(group,params.nodes[0]);
		});

		network.on("selectNode", function (params) {
			if(adding == false){
				adding = true;
				from_node = params.nodes[0];
			} else {
				adding = false;
				to_node = params.nodes[0];
				var index =	group.edges.findIndex(function(el) {
					return (el.to == from_node && el.from == to_node ||
						el.to == to_node && el.from == from_node)
					});
					if (index == -1){
						if (from_node != to_node){
							group.edges.push({from:from_node,to:to_node});
							update_network(group);
						};
					};
				}
			});

		};

		function update_group_network(groups,edges_of_groups){
			var adding = false;
			var from_node = 0;
			var to_node = 0;

			// adding the overall group edges to the edge array
			group_nodes = [];
			groups.forEach(function(group) {
				node_dict = {id: group.name, label: group.name, group: group.name};
				group_nodes.push(node_dict)
			});

			var data = {
				nodes: group_nodes,
				edges: edges_of_groups
			};

			var container = document.getElementById('group_network');
			var network = new vis.Network(container, data, options);
			network.on("selectEdge", function (params) {
				var index =	edges_of_groups.findIndex(function(edge) {
					return (edge.id == params.edges[0]);
				});
				edges_of_groups.splice(index,1);
				update_group_network(groups,edges_of_groups)
			});
			network.on("selectNode", function (params) {
				if(adding == false){
					adding = true;
					from_node = params.nodes[0];
				} else {
					adding = false;
					to_node = params.nodes[0];
					var index =	edges_of_groups.findIndex(function(el) {
						return (el.to == from_node && el.from == to_node ||
							el.to == to_node && el.from == from_node)
						});
						if(index == -1){
							if (from_node != to_node){
								edges_of_groups.push({from:from_node,to:to_node});
								update_group_network(groups,edges_of_groups);
							};
						};
					};
				});
			};
