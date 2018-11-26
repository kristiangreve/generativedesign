$(document).ready(generate_first_floorplans);
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

	console.log("max size for selection canvas: ", max_size);

	var factor_x = parseInt(room_selection_canvas.style.width) / max_size[1];
	var factor_y = parseInt(room_selection_canvas.style.height) / max_size[0];

	var scale_factor = Math.min(factor_x,factor_y);
	// var scale_factor = 1;

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
		text_name.fontSize = 10;
		text_name.justification = 'center';
		text_name.fontWeight = 'bold';
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
	console.log("max size in regular plot: ", max_size);

	var factor_x = parseInt(plotCanvas.style.width) / max_size[1];
	var factor_y = parseInt(plotCanvas.style.height) / max_size[0];
	var scale_factor = Math.min(factor_x,factor_y);

	// outline for the floor plan
	var outlineWidth = 3;
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
		path.fillColor = 'white';
		path.name = name;
		path.selected = false;
		path.opacity = 0.5;

		var text_name = new PointText(department.center);
		text_name.fillColor = 'black';
		text_name.fontSize = 10;
		text_name.justification = 'center';
		text_name.fontWeight = 'bold';
		text_name.content = name;

		var sign = new PointText(department.center);
		sign.fontSize = 50;
		sign.fillColor = 'white';
		sign.justification = 'center';
		sign.fontWeight = 'bold';
		sign.content = "";



		path.onMouseEnter = function(event) {
			if (this.selected == false){
				this.fillColor = 'green';
				sign.content = "+"

			} else if (this.selected == true){
				this.fillColor = 'red';
				sign.content = "-"
			}
			if (current_adjacency_department != ""){
				this.fillColor = 'yellow';
			}
		};

		// path.onDoubleClick = function(event){
		//	if (current_adjacency_department == this.name){
		//		current_adjacency_department = ""
		//	} else {
		//		current_adjacency_department = this.name;
		//		this.fillColor = 'blue';

		// 	};


		// };


		path.onClick = function(event) {
			var dict = {}
			dict.name = element.name
			dict.base = element.base
			dict.dims = element.dims
			// if it has not been clicked

			if (this.selected == false){
				this.selected = true;
				this.fillColor = 'green';
				selected_rooms.push(dict);
				// current_adjacency_department = name;
				console.log(selected_rooms)

			// if it has been clicked
		} else if (this.selected == true){
				this.fillColor = 'white';
				this.selected = false;
				selected_rooms.splice(selected_rooms.indexOf(dict), 1 );
				console.log(selected_rooms)
			};

			if (current_adjacency_department != ""){
				this.fillColor = 'orange';
			}

			// update selection canvas with new rooms
			update_room_selection_canvas();
		};

		path.onMouseLeave = function(event) {
			// like_button.visible = false;
			// if it has not been clicked
			sign.content = "";
			if (this.selected == false) {
				this.fillColor = 'white';
			} else if (this.selected == true) {
				this.fillColor = 'green';
			};

			if (current_adjacency_department == this.name) {
				this.fillColor = 'blue';
			};
		};

		// for plotting dimensions
		// var w = parse_dim(element.dims[1]);
		// var h = parse_dim(element.dims[0]);

		// var top_center = new Point(department.topCenter.x, department.topCenter.y+10)
		// var text_width = new PointText(top_center);

		// text_width.fillColor = 'black';
		// text_width.fontSize = 8;
		// text_width.justification = 'center';
		// text_width.content = w;

		// var line_to = new Path.Line(new Point(department.topLeft.x+4,department.topLeft.y+8), new Point(department.topCenter.x-2*w.length,department.topLeft.y+8));
		// var line_from = new Path.Line(new Point(department.topCenter.x+2*w.length,department.topRight.y+8), new Point(department.topRight.x-4,department.topRight.y+8));

		// line_to.strokeColor = 'grey';
		// line_from.strokeColor = 'grey';

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
