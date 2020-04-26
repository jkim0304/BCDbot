function drawSetsTable(table_cols){
	var markup = "";
	for(index in sorted_sets) {
		var set_name = sorted_sets[index][0]
		var score_sigmas = (sorted_sets[index][1]['max_clump_score'] - mean)/std

		var red = (Math.max(score_sigmas, 0))*255;
		var blue = (Math.max(-score_sigmas, 0))*255;
		var colorcss = '\"color:rgb(' + red + ',0,' + blue + ')\"'

		if(index % table_cols == 0) {
			markup += '<tr>';
		}
		markup += '<td style=' + colorcss + ' id=\"'+ encode(set_name) + '\" class=\"mtgset\">' + set_name + '</td>';
		if(index % table_cols == table_cols - 1) {
			markup += '</tr>';
		}

	}
	$('#sets-table').append(markup);
}

function drawPlayersNames() {
	var markup = '<tr>';
	for(player in players_picks) {
		markup += '<td class=\"name\"id=\"'+encode(player)+'\">' + player + '</td>'
	}
	$('#player-names').append(markup);
}

function resetSelection() {
	$('.selected').each(function(){
		$(this).removeClass('selected');
	});
}

function drawPlayerClumps(event, cols) {
	$('#set-data-table').empty();
	var cards_accessed = [];
	var legacy_unbans_accessed = [];
	var top_accessed = [];
	$('.selected').each(function(){
		$(this).removeClass('selected');
	});
	var pid = event["target"].id
	$('#' + pid).addClass('selected');
	var pname = unencode(event["target"].id);
	var picks = players_picks[pname]
	var total_clumps= []
	for(var p = 0; p < picks.length; p++) { 
		var setname = picks[p];
		legacy_unbans_accessed = legacy_unbans_accessed.concat(clumpscores_db[setname]['legacy_unbans']);
		top_accessed = top_accessed.concat(clumpscores_db[setname]['top_cards']);
		var id = encode(setname);
		$('#' + id).addClass('selected')
		var clump_data = clumpscores_db[setname]
		total_clumps = total_clumps.concat(clump_data['clumps']);
	}

	cards_accessed = cards_accessed.concat(legacy_unbans_accessed);
	for(var ti = 0; ti<top_accessed.length; ti++){
		if(!legacy_unbans_accessed.includes(top_accessed[ti])) {
			cards_accessed.push(top_accessed[ti]);
		}
	}
	cards_accessed_t = new Set(cards_accessed);
	cards_accessed = Array.from(cards_accessed_t);

	total_clumps.sort(function(a,b){
		if(a[2]<b[2]) {
			return -1;
		}
		else if(b[2] < a[2]) {
			return 1;
		} else {
			return b[3]-a[3];	
		}
	});
	for(var cl = 0; cl < total_clumps.length; cl++) {
		for(var c = 0; c < total_clumps[cl][0].length; c++) {
			cardname = total_clumps[cl][0][c];
			if(cards_accessed.includes(cardname)) {
				continue;
			} 
			cards_accessed.push(cardname);	
		}
	}
	//console.log(cards_accessed)
	var markup = "";
	for(var ci = 0; ci < cards_accessed.length; ci++){	
		if(ci % cols == 0) {
			markup += "<tr>";
		}
		markup += '<td><img src=\"'+card_index[cards_accessed[ci]]['art']+'\" id=\"'+encode(cards_accessed[ci])+'\" title=\"'+cards_accessed[ci]+'\"/></td>';
		if(ci % cols == cols-1) {
			markup += "</tr>";
		}
	}
	$('#set-data-table').append(markup);
	$('#set-data-table td img').each(function(){
			value = $('#cardsize')[0]['value'];
			$(this).css({'height':value + 'px'});		
	});
}

function drawSetData(event) {
	$('#set-data-table').empty();
	id = event["target"].id
	var name = unencode(id);
	$('#'+id).addClass('selected');
	//console.log(name);
	var data = clumpscores_db[name];
	var clumps = data['clumps']

	var already_seen = [];
	var markup = "<tr>";
	for(var lu = 0; lu < data['legacy_unbans'].length; lu++) {
		cardname = data['legacy_unbans'][lu];
		markup += '<td><img src=\"'+card_index[cardname]['art']+'\" id=\"'+encode(cardname)+'\" title=\"'+cardname+'\"/></td>';
	}
	markup += "</tr>";
	$('#set-data-table').append(markup);

	// Remove subclumps:
	clumps = ignoreSubclumps(clumps);
	// sort by powerlevel
	clumps.sort(function(a,b){
		return b[3]-a[3];
	});

	var markup = "<tr>";
	for(index in clumps) {
		if(index > 4){
			break
		}
		cards = clumps[index][0];
		if(checkSeen(already_seen, cards) == true) {
			continue
		}
		// visually sanitize against clumps we've seen entirely before
		for(var c = 0; c < cards.length; c++){	
			markup += '<td><img src=\"'+card_index[cards[c]]['art']+'\" id=\"'+encode(cards[c])+'\" title=\"'+cards[c]+'\"/></td>';
		}
		markup += "</tr>";
		$('#set-data-table').append(markup);
		already_seen.push(cards);
		markup="<tr>";	
	}
	markup = "<tr>"
	for(var t = 0; t < data['top_cards'].length; t++){
		topname = data['top_cards'][t];
		if($('#'+encode(topname)).length == 0){
			markup += '<td><img src=\"'+card_index[topname]['art']+'\" id=\"'+encode(topname)+'\" title=\"'+topname+'\"/></td>';
		}
	}
	markup += "</tr>";
	$('#set-data-table').append(markup);
	$('#set-data-table td img').each(function(){
		value = $('#cardsize')[0]['value'];
		$(this).css({'height':value + 'px'});
	});
}
















