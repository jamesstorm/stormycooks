<?php
/*
Plugin Name: MD5Hash Custom Field
Description: Adds an MD5 hash text field to media objects and posts, and allows updating via the REST API.
Version: 1.1
Author: Your Name
*/

// Add custom field to the post editor
function md5hash_add_custom_meta_box() {
    add_meta_box(
        'md5hash_meta_box', // ID of the meta box
        'MD5 Hash', // Title of the meta box
        'md5hash_custom_meta_box_callback', // Callback to render the field
        ['post', 'page'], // Post types (add more if needed)
        'side', // Context (side, normal, etc.)
        'default' // Priority
    );
}
add_action('add_meta_boxes', 'md5hash_add_custom_meta_box');

// Callback function to render the field
function md5hash_custom_meta_box_callback($post) {
    // Retrieve current value of MD5 hash
    $md5hash_value = get_post_meta($post->ID, '_md5hash', true);
    ?>
    <label for="md5hash_field">MD5 Hash:</label>
    <input type="text" id="md5hash_field" name="md5hash_field" value="<?php echo esc_attr($md5hash_value); ?>" />
    <?php
}

// Save the custom field value when the post is saved
function md5hash_save_custom_meta_box_data($post_id) {
    if (array_key_exists('md5hash_field', $_POST)) {
        update_post_meta(
            $post_id,
            '_md5hash',
            sanitize_text_field($_POST['md5hash_field'])
        );
    }
}
add_action('save_post', 'md5hash_save_custom_meta_box_data');

// Add custom field to media attachment editor
function md5hash_add_attachment_field( $form_fields, $post ) {
    // Add the MD5 Hash field to media objects
    $form_fields['md5hash_field'] = array(
        'label' => 'MD5 Hash',
        'input' => 'text',
        'value' => get_post_meta( $post->ID, '_md5hash', true ),
        'helps' => 'Enter the MD5 hash for this media item',
    );
    return $form_fields;
}
add_filter( 'attachment_fields_to_edit', 'md5hash_add_attachment_field', 10, 2 );

// Save custom field data for media attachments
function md5hash_save_attachment_field( $post, $attachment ) {
    if( isset( $attachment['md5hash_field'] ) ) {
        update_post_meta( $post['ID'], '_md5hash', sanitize_text_field( $attachment['md5hash_field'] ) );
    }
    return $post;
}
add_filter( 'attachment_fields_to_save', 'md5hash_save_attachment_field', 10, 2 );

// Register the MD5 hash meta field for posts and media attachments and allow API updates
function md5hash_register_meta() {
    // Register meta for posts
    register_post_meta( '', '_md5hash', array(
        'type'         => 'string',
        'description'  => 'MD5 Hash for posts or media',
        'single'       => true,
        'show_in_rest' => array(
            'schema' => array(
                'type' => 'string',
            ),
            'get_callback'    => null, // Optional if you want to customize the GET behavior
            'update_callback' => null, // Optional if you want to customize the UPDATE behavior
        ),
        'auth_callback' => function() {
            return current_user_can( 'edit_posts' ); // Ensure user has permission to edit posts
        },
    ));
}
add_action( 'rest_api_init', 'md5hash_register_meta' );

// Expose MD5 hash via REST API for posts and media
function md5hash_expose_meta_via_rest( $response, $post, $request ) {
    $md5hash = get_post_meta( $post->ID, '_md5hash', true );
    $response->data['md5hash'] = $md5hash;
    return $response;
}
add_filter( 'rest_prepare_post', 'md5hash_expose_meta_via_rest', 10, 3 );
add_filter( 'rest_prepare_attachment', 'md5hash_expose_meta_via_rest', 10, 3 );

