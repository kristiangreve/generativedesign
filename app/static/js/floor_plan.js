
var mypapers = [];
var selected_rooms_render = [];
var previously_selected_rooms_render = [];
var selected_rooms = [];
var current_adjacency_department = [];
var room_selection_papers = [];
var current_group = [];
var specified_rooms = [];
var render_array = [];
var group_id = 0;
// setup canvases
$(document).ready(setup_canvases_as_projects);


// $(document).ready(setup_room_selection_canvas);

function setup_canvases_as_projects(){
	var canvases = jQuery.makeArray($(".floor_canvas"));
	canvases.forEach(function(element){
		var newpaper = new paper.PaperScope();
		newpaper.setup(element);
		mypapers.push(newpaper);
	});
	generate_first_floorplans();
};

function setup_room_selection_canvas(){
	room_selection_canvas = document.getElementById("selection_canvas");
	var room_selection_paper = new paper.PaperScope();
	room_selection_paper.setup(room_selection_canvas);
	room_selection_papers.push(room_selection_paper);
};

function generate_first_floorplans() {
	$.post('/generate_first_floorplans/',{
		pop_size:0,
		generations:0
	}).done(function(response) {
		render_array = response;
		render_floorplans(render_array);
	});
};

function render_floorplans(render_array) {
	canvases = jQuery.makeArray($(".floor_canvas"));
	for( var i = 0; i< canvases.length; i++){
		canvases[i].setAttribute('plan_id',render_array[i]['id']);
		plotPlan(canvases[i],i,render_array[i]);
	};
};

// function to shorten floats to two decimals
function parse_dim(float) {
	return parseFloat(Math.round(float * 100) / 100).toFixed(2);
};

function update_nodes() {
	var unique_nodes = [];
	edges.forEach(function(element){
		unique_nodes.push(element.to);
		unique_nodes.push(element.from);
	});

	unique_nodes = Array.from(new Set(unique_nodes));
	nodes = [];
	unique_nodes.forEach(function(element){
		node_dict = {};
		node_dict.id = element;
		node_dict.label = element;
		node_dict.shape = 'dot';
		node_dict.color = 'lightgreen';
		nodes.push(node_dict)
	})
	console.log("nodes: ",nodes);

};

function add_nodes(group,group_id){
	group.forEach(function(element){
		node_dict = {};
		node_dict.group = group_id;
		node_dict.id = element;
		node_dict.label = element;
		node_dict.color = 'lightgreen';
		nodes.push(node_dict)
	});
	update_adjacency_graph();
};

function is_adjacent(department1,department2) {
	var edgeIndex =	edges.findIndex(function(element) {
		return (element.to == department2 && element.from == department1 || element.to == department1 && element.from == department2);
	});
	return edgeIndex;
};

function add_adjacent(department1,department2) {
	edge_dict = {};
	edge_dict.to = department1;
	edge_dict.from = department2;
	if(department1 != department2){
		edges.push(edge_dict);
	};
	update_nodes();
	update_adjacency_graph();
};

function remove_adjacent(department1,department2) {
	edgeIndex = is_adjacent(department1,department2);
	edges.splice(edgeIndex, 1);
	update_nodes();
	update_adjacency_graph();
};

function plotPlan(plotCanvas,project_id,render_graphics) {
	mypapers[project_id].activate();
	mypapers[project_id].view.draw();
	var layer = new Layer();
	mypapers[project_id].project.clear()
	mypapers[project_id].project.addLayer(layer)
	var departments = render_graphics.departments;
	// global variable max size

	max_size = render_graphics.max_sizes;
	var factor_x = parseInt(plotCanvas.style.width) / max_size[1];
	var factor_y = parseInt(plotCanvas.style.height) / max_size[0];
	var scale_factor = Math.min(factor_x,factor_y);

	// outline for the floor plan
	var outlineWidth = 2;
	var base = new Point(0,0);
	var dims = new Size(max_size[1]*scale_factor,max_size[0]*scale_factor)

	var outline = new Rectangle(base,dims);
	var path = new Path.Rectangle(outline);
	path.strokeColor = 'black';
	path.strokeWidth = outlineWidth;

	departments.forEach(function(element) {
		var base = new Point(element.base[0]*scale_factor,element.base[1]*scale_factor);
		var dims = new Size(element.dims[1]*scale_factor,element.dims[0]*scale_factor);
		var name = element.name;
		var department = new Rectangle(base,dims);
		var path = new Path.Rectangle(department);

		path.strokeColor = 'black';
		path.strokeWidth = 1;
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

		// Mouse over events //

		path.onMouseEnter = function(event) {
			this.fillColor = 'lightgreen';
		};

		path.onClick = function(event) {
			// if it is in the current group, remove
			index = current_group.indexOf(this.name)
			console.log("index: ",index);
			if (index > -1){
				current_group.splice(index,1);
				this.fillColor = 'lightgrey';
			} else {
				current_group.push(this.name);
				this.fillColor = 'green';
			};
			console.log(current_group);
		};

		path.onMouseLeave = function(event) {
			index = current_group.indexOf(this.name)
			// if it is in the group
			if (index > -1){
				this.fillColor = 'green';
			} else {
				this.fillColor = 'lightgrey';
			};
		};

	});
};

// on click on group group_button
$("#group_button").click(function(){
	console.log(current_group);
	add_nodes(current_group,group_id)
	group_id++;
	current_group = [];
	render_floorplans(render_array);

});



// on click on confirm button
$("#confirm_button").click(function(){
	// register what generation and index the solution had
	var plan_id = $(this).attr('plan_id');
	// make ajax call to generate new floor plans
	$.post('/generate_new_floorplans/',{
		selected_rooms: JSON.stringify(selected_rooms),
		nodes: JSON.stringify(nodes),
		edges: JSON.stringify(edges)
	}).done(function(response) {
		render_floorplans(response);
		for (var i=0; i < selected_rooms_render.length ; i++) {
			selected_rooms_render[i].color = 'grey';
			update_room_selection_canvas();

		};

	});
});
