
// handler for button to generate new population from 0
$("#generate_button").click(function(){
	$.post('/generate_first_floorplans/',{
		pop_size:0,
	}).done(function(response) {
		render_floorplans();
	});
};

// on click on floor plan
$(".floorcanvas").click(function(){
	// register what generation and index the solution had
	var generation = $(this).attr('generation')
	var generation_rank = $(this).attr('generation_rank')

	// make ajax call to generate new floor plans

	$.post('/generate_new_floorplans/',{
		generation: generation,
		generation_rank: generation_rank
	}).done(function(response) {
		render_floorplans(response.generations);
	});
});

function render_floorplans(graphics_array) {
	canvases = jQuery.makeArray($(".floorcanvas"));
	for(i = 0; i <= graphics_array.length; i ++){
		plotPlan(canvases[i],graphics_array[i]);
		canvases[i].setAttribute('id', graphics_array.id);
	}
};

// function to shorten floats to two decimals
function parse_dim(float) {
	return parseFloat(Math.round(float * 100) / 100).toFixed(2);
};

// function to plot graphics to a given canvas
function plotPlan(plotCanvas,graphics) {
		var scope = new paper.PaperScope();
		var canvas = document.getElementById(plotCanvas.id);
		scope.setup(canvas);
		scope.activate();
		var departments = graphics.departments;
		var max_size = graphics.max_sizes;
		// factors for scaling the rectangles and draw outside rectangle
		var factor_x = view.viewSize.width/max_size[1]
		var factor_y = view.viewSize.height/max_size[0]

		// outline for the floor plan
		var base = new Point(0,0)
		var dims = new Size(view.viewSize.width,view.viewSize.height)
		var outline = new Rectangle(base,dims);
		var path = new Path.Rectangle(outline);
		path.strokeColor = 'black';
		path.strokeWidth = 5;

		departments.forEach(function(element) {
			var base = new Point(element.base[0]*factor_x,element.base[1]*factor_y);
			var dims = new Size(element.dims[1]*factor_x,element.dims[0]*factor_y);
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
		};
	};
