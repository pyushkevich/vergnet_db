function printQuery(){
	var query = document.getElementById("Queries").value;
	if (query!='default'){
		jQuery.ajax({
			type:'get',
			url:'/temp/query_sample/'+query,
			cache:false,
			success: function(data) {
				document.getElementById("query_intro").innerHTML = "This query looks like this in Neo4j:";
				document.getElementById("query_table").classList.add("pure-table");
				document.getElementById("query_table").classList.add("pure-table-bordered");
				document.getElementById("query_text").innerHTML = data
			},
			error: function(request, status, error) {
				console.log('error')
			}
		});
	}else{
		document.getElementById("query_intro").innerHTML = "";
		document.getElementById("query_text").innerHTML = '';
		document.getElementById("query_table").classList.remove("pure-table");
		document.getElementById("query_table").classList.remove("pure-table-bordered");
	}	
}	