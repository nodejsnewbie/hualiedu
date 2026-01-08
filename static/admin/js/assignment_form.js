/**
 * Assignment Form Dynamic Field Display
 * 
 * This script handles dynamic field visibility based on storage_type selection
 * in the Assignment admin form.
 */

(function($) {
    'use strict';

    $(document).ready(function() {
        // Get the storage_type field
        var $storageType = $('#id_storage_type');
        
        if ($storageType.length === 0) {
            return; // Not on assignment form
        }

        // Get the fieldsets
        var $gitFieldset = $('.git-storage-fields').closest('.form-row').parent();
        var $filesystemFieldset = $('.filesystem-storage-fields').closest('.form-row').parent();

        // Function to toggle field visibility
        function toggleFields() {
            var storageType = $storageType.val();
            
            if (storageType === 'git') {
                // Show Git fields, hide filesystem fields
                $gitFieldset.show();
                $filesystemFieldset.hide();
                
                // Make Git URL required
                $('#id_git_url').prop('required', true);
                $('#id_base_path').prop('required', false);
            } else if (storageType === 'filesystem') {
                // Show filesystem fields, hide Git fields
                $gitFieldset.hide();
                $filesystemFieldset.show();
                
                // Make Git URL not required
                $('#id_git_url').prop('required', false);
                $('#id_base_path').prop('required', false);
            } else {
                // Hide both if no selection
                $gitFieldset.hide();
                $filesystemFieldset.hide();
            }
        }

        // Initial toggle
        toggleFields();

        // Toggle on change
        $storageType.on('change', toggleFields);
    });
})(django.jQuery);
