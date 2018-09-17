$(function(){
    $('body').on({
        mousemove: function(e){
            var $this = $(this);
            // Calculate number of stars
            var currentMousePosition = e.pageX - $this.offset().left;
            var width = $this.width();
            var rounded = Math.round((currentMousePosition/width)*10);

            var starNumber = rounded/2;

            // Remove + add Classes + Store current rating
            $this.removeClass().addClass('stars s-' + starNumber).attr('data-rating', starNumber);
        },
        mouseleave:function(){
            var $this = $(this); 
            $this.removeClass().addClass('stars s-' + $this.attr('data-default'));
        },
        click: function(){
            var $this = $(this);
            //Hide the current rating selector
            $this.replaceWith($('<div>', {
             'class': 'loading'
            }));

            // Send the request
            $.post('rating.php',{
                rating: $this.attr('data-rating')
            }, function(d){
                // Handle response
                if(d.result == 'error'){
                    alert(d.msg);
                } else {
                    $this.removeClass().addClass('stars s-' + d.rating).attr('data-default', d.rating)
                    $('.loading').replaceWith($this);
                }
            }, 'json');
        }
    }, '.stars');
});