// create a network
var container = document.getElementById('mynetwork');

var data = {
	nodes: nodes,
	edges: edges
};

var options = {};

function update_adjacency_graph(){
	var network = new vis.Network(container, data, options);
	console.log("adjacency graph updated")

};
