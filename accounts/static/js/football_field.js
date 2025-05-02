document.addEventListener('DOMContentLoaded', function() {
  const markers = document.querySelectorAll('.position-marker');
  const positionsInput = document.getElementById('positions-input') || document.querySelector('input[name="positions"]');
  const selectedDisplay = document.getElementById('selected-positions-display');
  const primaryDisplay = document.getElementById('primary-position-display');

  let selectedPositions = [];
  let primaryPosition = null;

  // Initialize from existing value if present
  if (positionsInput && positionsInput.value) {
    const positions = positionsInput.value.split(',').filter(Boolean);
    selectedPositions = positions;
    if (positions.length > 0) {
      primaryPosition = positions[0];
    }
    updateUI();
  }

  markers.forEach(marker => {
    marker.addEventListener('click', function() {
      const position = this.dataset.position;
      if (selectedPositions.includes(position)) {
        // If already selected, check if it's primary
        if (primaryPosition === position) {
          // Remove primary status but keep selected
          primaryPosition = null;
        } else {
          // Make it primary if already selected but not primary
          primaryPosition = position;
        }
      } else {
        // Add to selected positions
        selectedPositions.push(position);
        // If no primary position set, make this the primary
        if (!primaryPosition) {
          primaryPosition = position;
        }
      }
      updateUI();
    });
    // Right-click to remove
    marker.addEventListener('contextmenu', function(e) {
      e.preventDefault();
      const position = this.dataset.position;
      // Remove from selected positions
      selectedPositions = selectedPositions.filter(p => p !== position);
      // If it was primary, reset primary
      if (primaryPosition === position) {
        primaryPosition = selectedPositions.length > 0 ? selectedPositions[0] : null;
      }
      updateUI();
    });
  });

  function updateUI() {
    // Update markers
    markers.forEach(marker => {
      const position = marker.dataset.position;
      marker.classList.remove('selected', 'primary');
      if (selectedPositions.includes(position)) {
        marker.classList.add('selected');
        if (position === primaryPosition) {
          marker.classList.add('primary');
        }
      }
    });
    // Update hidden input - primary position first, then others
    let orderedPositions = [];
    if (primaryPosition) {
      orderedPositions.push(primaryPosition);
      orderedPositions = orderedPositions.concat(
        selectedPositions.filter(p => p !== primaryPosition)
      );
    } else {
      orderedPositions = [...selectedPositions];
    }
    if (positionsInput) {
      positionsInput.value = orderedPositions.join(',');
    }
    // Update display
    if (selectedDisplay) {
      selectedDisplay.textContent = selectedPositions.length > 0 ? 
        selectedPositions.join(', ') : 'None';
    }
    if (primaryDisplay) {
      primaryDisplay.textContent = primaryPosition || 'None';
    }
  }
}); 