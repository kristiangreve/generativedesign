// global variables
var mypapers = [];
var selected_rooms = [];
var current_adjacency_department = [];
var room_selection_papers = [];

// setup required canvases
$(document).ready(setup_canvases_as_projects);
$(document).ready(setup_room_selection_canvas);


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
	console.log("room selection canvas: ", room_selection_canvas);
	var room_selection_paper = new paper.PaperScope();
	room_selection_paper.setup(room_selection_canvas);
	room_selection_papers.push(room_selection_paper);
};

function generate_first_floorplans() {
	$.post('/generate_first_floorplans/',{
		pop_size:0,
		generations:0
	}).done(function(response) {
		render_floorplans(response);
	});
};

function update_room_selection_canvas() {
	room_selection_canvas = document.getElementById("selection_canvas");

	selection_paper = room_selection_papers[0]
	selection_paper.activate();
	selection_paper.view.draw();
	var layer = new Layer();
	selection_paper.project.clear()
	selection_paper.project.addLayer(layer)



	var factor_x = parseInt(room_selection_canvas.style.width) / max_size[1];
	var factor_y = parseInt(room_selection_canvas.style.height) / max_size[0];

	var scale_factor = Math.min(factor_x,factor_y);
	// var scale_factor = 1;


	// outline for the floor plan
	var outlineWidth = 1;
	var base = new Point(0,0);
	var dims = new Size(max_size[1]*scale_factor,max_size[0]*scale_factor)

	var outline = new Rectangle(base,dims);
	var path = new Path.Rectangle(outline);
	path.strokeColor = 'black';
	path.strokeWidth = outlineWidth;

	console.log("rendering selections with x factor: ", scale_factor);

	selected_rooms.forEach(function(element) {
		var base = new Point(element.base[0]*scale_factor,element.base[1]*scale_factor);
		var dims = new Size(element.dims[1]*scale_factor,element.dims[0]*scale_factor);

		var department = new Rectangle(base,dims);
		var path = new Path.Rectangle(department);

		path.fillColor = 'green';
		path.opacity = 0.2;

		var text_name = new PointText(department.center);
		text_name.fillColor = 'black';
		text_name.fontSize = 8;
		text_name.justification = 'center';
		text_name.content = element.name;


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
}


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

			if (current_adjacency_department == ""){
				// iterate the list of selected rooms to see if this floor plan is in it
				// first see if name is the same, then base point to compare
				selected = false;
				for (var i = 0; i < selected_rooms.length ; i++) {
					if (selected_rooms[i].name == element.name) {
						if (selected_rooms[i].base == element.base) {
							selected = true;
							break;
						};
					};
				};

				if (selected == false){
					this.fillColor = 'green';
				} else if (selected == true){
					this.fillColor = 'red';
				}
			} else {
				this.fillColor = 'orange';
			}

		};


		path.onClick = function(event) {

			var dict = {}
			dict.name = element.name
			dict.base = element.base
			dict.dims = element.dims

			if (current_adjacency_department == ""){
				// iterate the list of selected rooms to see if this floor plan is in it
				// first see if name is the same, then base point to compare
				selected = false;
				for (var i = 0; i < selected_rooms.length ; i++) {
					if (selected_rooms[i].name == element.name) {
						if (selected_rooms[i].base == element.base) {
							selected = true;
							// if it has been selected, remove it from the list of selections
							selected_rooms.splice(i, 1);
							break;
						};
					};
				};
				if (selected == false) {
					// iterate selections to see if an element with identical name already exists
					for (var i=0; i < selected_rooms.length ; i++) {
						if (selected_rooms[i].name == element.name) {
							selected_rooms.splice(i, 1);
							break;
						}
					};
					selected_rooms.push(dict);
				};

				console.log(selected_rooms);
			} else {

				// add edge between nodes
				edge_dict = {};
				edge_dict.from = current_adjacency_department;
				edge_dict.to = name;


				if(current_adjacency_department != name){
					edges.push(edge_dict);
				};


				// add "from node" to array
				node_dict = {};
				node_dict.id = current_adjacency_department;
				node_dict.label = current_adjacency_department;
				node_dict.fixed = true;
				node_dict.shape = 'circle';
				node_dict.color = '#d3d3d3';
				// if it is not in the array already

				already_in_array = false;
				for (var i=0; i < nodes.length ; i++) {
					console.log(nodes[i]);
					if (nodes[i].id == node_dict.id) {
						already_in_array = true;
						break;
					}
				};

				if (already_in_array == false){
					nodes.push(node_dict);
				}


				// add "to node" to array
				node_dict = {};
				node_dict.id = name;
				node_dict.label = name;
				node_dict.fixed = true;
				node_dict.shape = 'circle';
				node_dict.color = '#d3d3d3';

				already_in_array = false;
				for (var i=0; i < nodes.length ; i++) {
					if (nodes[i].id == node_dict.id) {
						already_in_array = true;
						break;
					}
				};

				if (already_in_array == false){
					nodes.push(node_dict);
				}

				console.log("edges: ", edges);
				console.log("nodes: ", nodes);

				update_adjacency_graph();

			};
			update_room_selection_canvas();
		};

		path.onDoubleClick = function(event){
			// check if this department is currently the one being specified

			if (current_adjacency_department == this.name){
				current_adjacency_department = "";
			} else if (current_adjacency_department == ""){
				current_adjacency_department = this.name;
				this.fillColor = 'blue';
			} else {
				// if there is another department currently being specified
			};
		};


		path.onMouseLeave = function(event) {
			if (current_adjacency_department == this.name){
				this.fillColor = 'blue';
			} else {
				// if there is another department currently being specified
				this.fillColor = 'lightgrey';
			};
		};
	});
};

// on click on confirm button
$("#confirm_button").click(function(){
	// register what generation and index the solution had
	var plan_id = $(this).attr('plan_id');

	// make ajax call to generate new floor plans
	$.post('/generate_new_floorplans/',{
		selected_rooms: JSON.stringify(selected_rooms)
	}).done(function(response) {
		render_floorplans(response);
		selected_rooms = [];
	});
});
