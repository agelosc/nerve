$(document).ready(function(){
	const csrftoken = Cookies.get('csrftoken');

		// BROWSE
		$(".browse").click(function(event){
			var input = $(this).prev();
			event.preventDefault();

			$.ajax({
				headers: { "X-CSRFToken": csrftoken },
				type: "POST",
				url: "/browse",
				data: {"ajax":true},
				success: function(b) {
					if(b != "")
					{
						input.val(b);
					}
				}
			});
		});

});
