// handler for button to generate new population from 0

$(document).ready(generate_first_floorplans);
var mypapers = []
$(document).ready(setup_canvases_as_projects);
function setup_canvases_as_projects(){
	var canvases = jQuery.makeArray($(".floorcanvas"));
	canvases.forEach(function(element){
		var newpaper = new paper.PaperScope();
		newpaper.setup(element);
		mypapers.push(newpaper);
	});
};

// $("#generate_button").click(generate_first_floorplans);

function generate_first_floorplans() {
	$.post('/generate_first_floorplans/',{
		pop_size:0,
		generations:0
	}).done(function(response) {
		render_floorplans(response);
	});
};

// on click on floor plan
$(".floorcanvas").click(function(){
	// register what generation and index the solution had
	var plan_id = $(this).attr('plan_id')
	// make ajax call to generate new floor plans
	$.post('/generate_new_floorplans/',{
		id: plan_id
	}).done(function(response) {
		render_floorplans(response);
	});
});

function render_floorplans(render_array) {
	canvases = jQuery.makeArray($(".floorcanvas"));
	for( var i = 0; i< render_array.length; i++){
		canvases[i].setAttribute('plan_id',render_array[i]['id']);
		plotPlan(canvases[i],i,render_array[i]);
	};
};

// function to shorten floats to two decimals
function parse_dim(float) {
	return parseFloat(Math.round(float * 100) / 100).toFixed(2);
}

function plotPlan(plotCanvas,project_id,render_graphics) {
	console.log(plotCanvas);
	mypapers[project_id].activate();
	mypapers[project_id].view.draw();
	var layer = new Layer();
	mypapers[project_id].project.clear()
	mypapers[project_id].project.addLayer(layer)


	var departments = render_graphics.departments;
	var max_size = render_graphics.max_sizes;

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

		// for plotting dimensions
		var w = parse_dim(element.dims[1]);
		var h = parse_dim(element.dims[0]);

		var text_name = new PointText(department.center);
		text_name.fillColor = 'black';
		text_name.fontSize = 10;
		text_name.justification = 'center';
		text_name.fontWeight = 'bold';
		text_name.content = name;

		var top_center = new Point(department.topCenter.x, department.topCenter.y+10)
		var text_width = new PointText(top_center);

		text_width.fillColor = 'black';
		text_width.fontSize = 8;
		text_width.justification = 'center';
		text_width.content = w;

		var line_to = new Path.Line(new Point(department.topLeft.x+4,department.topLeft.y+8), new Point(department.topCenter.x-2*w.length,department.topLeft.y+8));
		var line_from = new Path.Line(new Point(department.topCenter.x+2*w.length,department.topRight.y+8), new Point(department.topRight.x-4,department.topRight.y+8));

		line_to.strokeColor = 'grey';
		line_from.strokeColor = 'grey';

	});
};
