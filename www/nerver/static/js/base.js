$(document).ready(function(){
    const csrftoken = Cookies.get('csrftoken');

    // Tooltips
    $(function () {
        $('[data-toggle="tooltip"]').tooltip({
            boundary: 'window',
            container: 'body'
        })
    })

    $('.dropdown-toggle').on('click', null, function(){
        $(this).dropdown('toggle');
    });    

    // Dropdown selection
    function selectDropdown(obj) {
        const target = $(obj).data('target');
        $(target).html( $(obj).html() + ' ' );
        $(target).dropdown('toggle');
    }

    $('.asset .dropdown-item').click( function(){
        selectDropdown(this);
        assetUpdate(this);
    });
    
    //$('.asset .dropdown-item').click(function(event){
    
    function assetUpdate(obj){
        const anchor = $(obj).data('anchor');
        const key = $(obj).data('key');
        const val = $(obj).data('val')

        var url = new URL( $(anchor).prop('href') );
        url.searchParams.set(key, val);
        if(key == 'version'){
            url.searchParams.delete('format')
        }
        var href = url.pathname + decodeURIComponent(url.search);
        $(anchor).attr('href', href)
        window.history.replaceState(null, document.title, href);
        $.ajax({
            headers: { "X-CSRFToken": csrftoken },
            type: "POST",
            url: "/action",
            data: {"ajax":true, "action":"asset", "url":href},
            success: function(b){
                $('#comment').html(b.comment);
                $('#user').val(b.user);
                $('#date').val(b.date);

                if(key=='version'){
                    var btn = $('#formats');
                    var menu = $('#formats').next();

                    $(btn).html(b.formatlong + ' ')
                    $(menu).empty();
                    for( const [k,v] of Object.entries(b.formats)){
                        const item = document.createElement('a')
                            
                        item.className = 'dropdown-item';
                        item.href='#';
                        item.dataset.target='#formats';
                        item.dataset.anchor = '#asset-url'
                        item.dataset.key = "format";
                        item.dataset.val = k
                        item.innerText = v
                        $(item).appendTo(menu).click(function(){
                            selectDropdown(item);
                            assetUpdate(item);
                        });
                    }
                }
            }
        });

    }

    function updateAsset(event){
        //event.preventDefault();
        const anchor = $(this).data('anchor');
        const key = $(this).data('key');
        const val = $(this).data('val');

        var href = $(anchor).prop('href');
        var url = new URL(href);
        url.searchParams.set(key, val )
        var result = url.pathname + decodeURIComponent(url.search);
        $(anchor).attr('href', result);
        //window.history.replaceState(null, document.title, result);

        $.ajax({
			headers: { "X-CSRFToken": csrftoken },
			type: "POST",
			url: "/action",
			data: {"ajax":true, "action":"asset", "url":result},
			success: function(b) {
				if(b != "")
				{
                    $('#comment').html(b["comment"])
                    $('#user').val(b["user"])
                    $('#date').val(b["date"])

                    if(key == 'format')
                    {
                        
                    }

                    if(key == 'version')
                    {
                        
                        var button = $('#formats');
                        button.html(b.formatlong);
                        var menu = $('#formats').next();
                        $(menu).empty();
                        for( const [k, v] of Object.entries(b.formats))
                        {   
                            //<a class="dropdown-item" href="#" data-target="#formats" data-anchor="#asset-url" data-key="format" data-val={{format}}>{{formatlong}}</a>
                            const anchor = document.createElement('a')
                            
                            anchor.className = 'dropdown-item';
                            anchor.href='#';
                            anchor.dataset.target='#formats';
                            anchor.dataset.anchor = '#asset-url'
                            anchor.dataset.key = "format";
                            anchor.dataset.val = k
                            anchor.innerText = v
                            $(anchor).appendTo(menu).click(updateAsset);
                            //$(anchor).appendTo(menu).click(toggleDropdown);
                            //$(anchor).appendTo(menu).click(selectDropdown);
                            
                        }
                    }
                    //console.log(b)
                    
				}
			}            
        });
    };
    //$('.asset .dropdown-item').on('click', null, updateAsset );
    



    // Modals
    $('[data-toggle="modal"]').click( function(event) {
        var data = $(this).data()
        $(data['target']).modal('show');
    });

    // Modal: Dismiss
    $('.modal-dismiss').click( function() {
        const target = $(this).data('dismiss');
        $(target).modal('hide');
    });

    // Modal: Job Edit
    $('a.job-edit').click( function(event){
        $('.modal-title').html( $(this).data('jobpath') );
        $('#job-name').val( $(this).data('jobname') );
        $('#job-path').val( $(this).data('jobpath') );

        event.preventDefault();
        $('#job-edit').modal('show');

    });

    // Actions
    $('.action').click(function(){
        var data = $(this).data();
        $.ajax({
            headers: { "X-CSRFToken": csrftoken },
            type: "POST",
            url: "/action",
            data: data,
            success: function(b){
                if(b != "")
                {
                    $(data['htmltarget']).html(b)
                    //console.log(b)
                }
                if('reload' in data && data['reload'] == 1)
                {
                    location.reload()
                }
            }
        });
        
    });

    // Job App REMOVE
    $('.app2').click(function(){
        var path = $(this).data('path')
        var app = $(this).data('app')

        $.ajax({
			headers: { "X-CSRFToken": csrftoken },
			type: "POST",
			url: "app",
			data: {"ajax":true, "path":path, "app":app},
			success: function(b) {
				if(b != "")
				{
                    console.log(b)
                    /*
					var history = $(".footer .container").html();
					history = history.replace('class="console"', '')
					footer = '<span class="console">';
					footer+= b;
					footer+= '</span></br>';
					footer+= history;

					$(".footer .container").html( footer );
                    */
				}
			}            
        });

    });
})