$(document).ready(function(){
    const csrftoken = Cookies.get('csrftoken');


    $('.action').click(function(){
        var data = $(this).data();
        $.ajax({
            headers: { "X-CSRFToken": csrftoken },
            type: "POST",
            url: "action",
            async: false,
            data: data,
            success: function(b){
                if(b != "")
                {
                    console.log(b)
                }
                if('reload' in data){ location.reload() }
            }
        });
        
    });
    // App
    $('.app').click(function(){
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