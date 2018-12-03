var mypapers = [];

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

// button onclick handlers
$("#generate_button").click(function(){
	var mode = 'new';
	get_floorplans(mode,groups,edges_of_groups)
});

$("#add_group_button").click(function(){
	console.log("group added: ", current_group)

	// get name from field and delete it
	name = document.getElementById("name_of_group").value;
	document.getElementById("name_of_group").value = "";

	// add a card for the group
	add_group_card(name);
	group_dict = {name:name,rooms:current_group};
	init_group_adjacents(group_dict);
	groups.push(group_dict);

	// find index of element in groups array
	var index =	groups.findIndex(function(group) {
		return (group.name == name)
	});
	console.log
	// pass that array to the opdate network function
	update_network(groups[index]);
	current_group = [];
	console.log("groups", groups);
	update_group_network(groups,edges_of_groups);
	render_floorplans(render_array);
});

function init_group_adjacents(group){
	group.edges = []
	group.nodes = []

	group.rooms.forEach(function(element){
		node_dict = {id: element.name, label: element.name, group: group.name};
		group.nodes.push(node_dict);
		compare_and_add(group,element);
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


function render_floorplans(render_array) {
	canvases = jQuery.makeArray($(".floor_canvas"));
	for( var i = 0; i< canvases.length; i++){
		plotPlan(canvases[i],i,render_array[i]);
		canvases[i].setAttribute('plan_id',render_array[i].id); // ændret
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
	console.log("id of canvas: ", render_id);

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
		path.fillColor = 'lightgrey';
		path.name = name;
		path.selected = false;
		path.opacity = 0.5;

		var font_size = 12;
		var center_point = new Point(department.center._x,department.center._y);
		var text_name = new PointText(center_point);
		text_name.fillColor = 'black';
		text_name.fontSize = font_size;
		text_name.justification = 'center';
		text_name.content = name;

		var area_point = new Point(department.center._x,department.center._y+font_size);
		var text_area = new PointText(area_point);
		text_area.fillColor = 'black';
		text_area.fontSize = font_size;
		text_area.justification = 'center';
		text_area.content = parse_dim(element.dims[1]*element.dims[0]);


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
				department_dict.name = this.name;
				department_dict.plan_id = render_id;
				department_dict.render_id = project_id;
				console.log("canvas id: ", department_dict.plan_id)
				current_group.push(department_dict);
				this.fillColor = 'green';
			};
			console.log(current_group);
		};

		path.onMouseLeave = function(event) {
			var index =	current_group.findIndex(function(element) {
				return (element.name == name);
			});
			// if it is in the group
			if (index > -1){
				this.fillColor = 'green';
			} else {
				this.fillColor = 'lightgrey';
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
