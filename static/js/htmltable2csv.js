function toCsv(){
	var table = document.getElementById("result-table").innerHTML;
	var data = table.replace(/\s{2,}/g,'')
		.replace(/,/g,';')
		.replace(/<thead>/g,'')
		.replace(/<\/thead>/g,'')
		.replace(/<tbody>/g,'')
		.replace(/<\/tbody>/g,'')
		.replace(/<tr>/g,'')
		.replace(/<\/tr>/g,'\r\n')
		.replace(/<th>/g,'')
		.replace(/<\/th>/g,',')
		.replace(/<td>/g,'')
		.replace(/<\/td>/g,',')
		.replace(/\t/g,'')
		.replace(/\n/g,'');
	var myLink = document.createElement('a');
	myLink.download = "result.csv";
	myLink.href = "data:application/csv," + escape(data);
	myLink.click();
}

function toTsv(){
	var table = document.getElementById("result-table").innerHTML;
	var data = table.replace(/\s{2,}/g,'')
		<!--.replace(/,/g,';')-->
		.replace(/<thead>/g,'')
		.replace(/<\/thead>/g,'')
		.replace(/<tbody>/g,'')
		.replace(/<\/tbody>/g,'')
		.replace(/<tr>/g,'')
		.replace(/<\/tr>/g,'\r\n')
		.replace(/<th>/g,'')
		.replace(/\t/g,'')
		.replace(/<\/th>/g,'\t')
		.replace(/<td>/g,'')
		.replace(/<\/td>/g,'\t')	
		.replace(/\n/g,'');
	var myLink = document.createElement('a');
	myLink.download = "result.tsv";
	myLink.href = "data:application/csv," + escape(data);
	myLink.click();
}
	