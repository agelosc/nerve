$(document).ready(function(){
    const csrftoken = Cookies.get('csrftoken');

    // Tooltips
    $(function () {
        $('[data-toggle="tooltip"]').tooltip({
            boundary: 'window',
            container: 'body'
        })
    })
    
    // Dropdown selection
    function selectDropdown(obj) {
        const target = $(obj).data('target');
        $(target).html( $(obj).html() + ' ' );
        //$(target).dropdown('toggle');
    }

    $('.asset .dropdown-item').click( function(){
        selectDropdown(this);
    });

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
        //$('#job-edit').modal('show');

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