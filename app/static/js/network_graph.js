var nodes = [
	
];

// create an array with edges
var edges = [

];

// create a network
var container = document.getElementById('mynetwork');

var data = {
	nodes: nodes,
	edges: edges
};

var options = {};

function update_adjacency_graph(){
	var network = new vis.Network(container, data, options);

};

$(document).ready(update_adjacency_graph);
