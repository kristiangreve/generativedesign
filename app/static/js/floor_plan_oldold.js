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

// function for adding the latest group to form
// function add_to_form(current_group) {
// 	document.getElementById('group_form_hidden_field').value = current_group;
// };

// setup canvases
$(document).ready(setup_canvases);
$(document).ready(get_floorplans('restart'));

function setup_canvases(){
	var canvases = jQuery.makeArray($(".floor_canvas"));
	canvases.forEach(function(element){
		var newpaper = new paper.PaperScope();
		newpaper.setup(element);
		mypapers.push(newpaper);
	});
};

function get_floorplans(mode){
	$.post('/get_floorplans',{
		mode:mode
	}).done(function(response) {
		render_array = response;
		render_floorplans(render_array);
	});
};

// function ajax call to add a group
function manage_groups(action, name, group){
	$.post('/manage_groups',{
		action: action,
		name: name,
		group: JSON.stringify(group)
	}).done(function(response) {
		console.log("response from manage: ", response)
		location = location.href
	});
};

$("#add_group_button").click(function(){
	name = document.getElementById("name_of_group").value;

	manage_groups('add', name, current_group);
	current_group = [];

});

function render_floorplans(render_array) {
	canvases = jQuery.makeArray($(".floor_canvas"));
	for( var i = 0; i< canvases.length; i++){
		plotPlan(canvases[i],i,render_array[i]);
		canvases[i].setAttribute('plan_id',render_array[i].id); // ændret
	};
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

		var font_size_name = 12;
		var center_point = new Point(department.center._x,department.center._y);
		var text_name = new PointText(center_point);
		text_name.fillColor = 'black';

		text_name.fontSize = font_size_name;
		text_name.justification = 'center';
		text_name.content = name;

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

// function update_nodes_old() {
// 	var unique_nodes = [];
// 	edges.forEach(function(element){
// 		unique_nodes.push(element.to);
// 		unique_nodes.push(element.from);
// 	});
// 	unique_nodes = Array.from(new Set(unique_nodes));
// 	nodes = [];
// 	unique_nodes.forEach(function(element){
// 		node_dict = {};
// 		node_dict.id = element;
// 		node_dict.label = element;
// 		node_dict.color = 'lightgreen';
// 		nodes.push(node_dict)
// 	})
// };
//
// function update_nodes() {
// 	var unique_nodes = [];
// 	edges.forEach(function(element){
// 		unique_nodes.push(element.to);
// 		unique_nodes.push(element.from);
// 	});
// 	unique_nodes = Array.from(new Set(unique_nodes));
// 	nodes = [];
// 	unique_nodes.forEach(function(element){
// 		node_dict = {};
// 		node_dict.id = element;
// 		node_dict.label = element;
// 		node_dict.color = 'lightgreen';
// 		nodes.push(node_dict)
// 	})
// };
// function is_adjacent(department1,department2) {
// 	var edgeIndex =	edges.findIndex(function(element) {
// 		return (element.to == department2 && element.from == department1 || element.to == department1 && element.from == department2);
// 	});
// 	return edgeIndex;
// };
// function remove_adjacent(department1,department2) {
// 	edgeIndex = is_adjacent(department1,department2);
// 	edges.splice(edgeIndex, 1);
// };

//
// function add_nodes(){
// 	// iterate groups array
// 	groups.forEach(function(group){
// 		console.log("nodes: ", nodes);
// 		console.log("group: ", group);
// 		// iterate each group in that array
// 		group.departments.forEach(function(department){
// 			var index =	nodes.findIndex(function(node) {
// 				return (node.id == department.name);
// 			});
// 			node_dict = {};
// 			node_dict.group = group.group_id;
// 			node_dict.id = department.name;
// 			node_dict.label = department.name;
// 			if (index == -1){
// 				nodes.push(node_dict);
// 			};
// 		});
// 	});
// }

//
// function compare_and_add(current_department,array1,array2){
// 	array1.forEach(function(element1){
// 		array2.forEach(function(element2){
// 			if (element1.name == element2){
// 				add_adjacent(current_department,element2);
// 			};
// 		});
// 	});
// };
//
// function add_adjacent(department1,department2) {
// 	if (is_adjacent(department1,department2) == -1){
// 		edge_dict = {};
// 		edge_dict.to = department1;
// 		edge_dict.from = department2;
// 		if(department1 != department2){
// 			edges.push(edge_dict);
// 		};
// 	};
// };

// $("#group_button").click(function(){
// 	current_group.forEach(function(element){
// 		// compare the other group members to the currently adajcent rooms:
// 		var adajcent_rooms = render_array[element.render_id].all_adjacency_dict[element.name];
// 		current_department = element.name;
// 		compare_and_add(current_department,current_group,adajcent_rooms);
// 	});
//
// 	group_dict = {}
// 	group_dict.group_id = group_id;
// 	group_dict.departments = current_group;
// 	groups.push(group_dict);
// 	console.log(groups);
// 	group_id++;
//
// 	current_group = [];
// 	add_nodes();
// 	update_adjacency_graph();
// 	render_floorplans(render_array);
// });
//
// // on click on confirm button
// $("#confirm_button").click(function(){
// 	// register what generation and index the solution had
// 	var plan_id = $(this).attr('plan_id');
// 	// make ajax call to generate new floor plans
// 	$.post('/generate_new_floorplans/',{
// 		selected_rooms: JSON.stringify(selected_rooms),
// 		nodes: JSON.stringify(nodes),
// 		edges: JSON.stringify(edges),
// 		groups: JSON.stringify(groups)
// 	}).done(function(response) {
// 		render_floorplans(response);
// 		for (var i=0; i < selected_rooms_render.length ; i++) {
// 			selected_rooms_render[i].color = 'grey';
// 			update_room_selection_canvas();
//
// 		};
//
// 	});
// });


// function setup_room_selection_canvas(){
// 	room_selection_canvas = document.getElementById("selection_canvas");
// 	var room_selection_paper = new paper.PaperScope();
// 	room_selection_paper.setup(room_selection_canvas);
// 	room_selection_papers.push(room_selection_paper);
// };
// function generate_first_floorplans() {
// 	$.post('/generate_first_floorplans/',{
// 		pop_size:0,
// 		generations:0
// 	}).done(function(response) {
// 		render_array = response;
// 		render_floorplans(render_array);
// 	});
// };
// // function to shorten floats to two decimals
// function parse_dim(float) {
// 	return parseFloat(Math.round(float * 100) / 100).toFixed(2);
// };
