function loadAbout(){
	var url = window.location.href.toString();
	var str = "about";
	if (url.includes(str)){
		jQuery.ajax({
			type:'get',
			url:'/temp/about/',
			cache:false,
			//data:query,
			success: function(data) {
				var ul1 = document.getElementById("list-csv");
				var ul2 = document.getElementById("info-db");
				if (data != "([], [{'Relationships': 0}])"){
					temp = data.split("], [");
					var csvfiles = temp[0].replace(/\[|\(|'/g,"").split(",");
					var info = temp[1].replace(/\{|}|\)|\]|\[|'|NodeType|SampleSize|:/gi,"").split(",");
					var x;
					var i=0;
					var len = info.length;
					for (x in csvfiles){
						var li = document.createElement("li");
						li.appendChild(document.createTextNode(csvfiles[x].trim()));
						ul1.appendChild(li);
					};
					for (; i<len-1;){
						var li = document.createElement("li");
						li.appendChild(document.createTextNode(info[i].trim()+": "+info[i+1]+" nodes"));
						ul2.appendChild(li);
						i=i+2;
					};
					var rel = info[len-1].trim().split(" ");
					var li = document.createElement("li");
					li.appendChild(document.createTextNode(rel[1]+" "+rel[0]));
					ul2.appendChild(li);
				}else{
					var div1 = document.getElementById("csv-imported");
					var div2 = document.getElementById("db-info");
					var p1 = document.createElement("p");
					var p2 = document.createElement("p");
					p1.appendChild(document.createTextNode("The database is empty"));
					div1.replaceChild(p1,ul1);
					p2.appendChild(document.createTextNode("The database is empty"));
					div2.replaceChild(p2,ul2);
				}
			},
			error: function(request, status, error) {
				console.log('error')
			}
		});
	}
}