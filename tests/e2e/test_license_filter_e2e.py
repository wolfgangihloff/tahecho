#!/usr/bin/env python3
"""
End-to-end tests for the dynamic license filter functionality using Playwright.
These tests simulate real user interactions in a browser.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any


@pytest.fixture(scope="session")
def test_sbom_data() -> Dict[str, Any]:
    """Create sample SBOM data for testing."""
    return {
        "metadata": {
            "component": {
                "name": "test-app",
                "version": "1.0.0"
            }
        },
        "components": [
            {
                "name": "component-mit",
                "version": "1.0.0",
                "type": "library",
                "licenses": [{"license": {"id": "MIT", "name": "MIT License"}}]
            },
            {
                "name": "component-apache",
                "version": "2.0.0", 
                "type": "library",
                "licenses": [{"license": {"id": "Apache-2.0", "name": "Apache License 2.0"}}]
            },
            {
                "name": "component-bsd",
                "version": "3.0.0",
                "type": "library", 
                "licenses": [{"license": {"id": "BSD-3-Clause", "name": "BSD 3-Clause License"}}]
            },
            {
                "name": "component-pypi-enhanced",
                "version": "1.5.0",
                "type": "library",
                "licenses": [{"license": {"id": "MIT", "name": "MIT (PyPI)"}}]
            },
            {
                "name": "component-no-license",
                "version": "0.1.0",
                "type": "library",
                "licenses": []
            }
        ]
    }


@pytest.mark.asyncio
async def test_license_filter_real_interaction(page: Any, test_sbom_data: Dict[str, Any]) -> None:
    """Test the complete license filter workflow with real user interactions."""
    
    # Navigate to the page served by our HTTP server
    await page.goto("http://localhost:8000/public/index.html")
    
    # Wait for the page to load
    await page.wait_for_load_state("networkidle")
    
    # Verify the page loaded correctly
    await page.wait_for_selector("#load-sbom-btn")
    
    # Create a test SBOM file that the page can actually load
    sbom_file = Path("/Users/wolfgang.ihloff/workspace/tahecho/public/test_sbom.json")
    with open(sbom_file, 'w') as f:
        json.dump(test_sbom_data, f, indent=2)
    
    try:
        # Modify the page to load our test SBOM instead of the regular one
        await page.evaluate("""
            // Override the fetch to use our test data
            const originalFetch = window.fetch;
            window.fetch = async function(url) {
                if (url.includes('sbom.json')) {
                    return originalFetch('/public/test_sbom.json');
                }
                return originalFetch(url);
            };
        """)
        
        # Click the load SBOM button
        await page.click("#load-sbom-btn")
        
        # Wait for the SBOM data to load and the components section to appear
        await page.wait_for_selector("#components-section", state="visible")
        
        # Wait for the license filter to be populated
        await page.wait_for_function("""
            () => {
                const select = document.getElementById('license-filter');
                return select && select.options.length > 1; // More than just "All Licenses"
            }
        """)
        
        # Check that the license filter was populated with the expected licenses
        license_options = await page.evaluate("""
            () => {
                const select = document.getElementById('license-filter');
                return Array.from(select.options).map(option => ({
                    value: option.value,
                    text: option.text
                }));
            }
        """)
        
        print(f"License options found: {license_options}")
        
        # Should have: All Licenses, MIT, Apache-2.0, BSD-3-Clause, Unknown/Not Specified
        expected_licenses = {"", "MIT", "Apache-2.0", "BSD-3-Clause", "Unknown/Not Specified"}
        actual_license_values = {option["value"] for option in license_options}
        
        assert expected_licenses.issubset(actual_license_values), f"Missing licenses. Expected {expected_licenses}, got {actual_license_values}"
        
        # Wait for table to be populated
        await page.wait_for_selector("#components-tbody tr")
        
        # Get initial row count
        initial_rows = await page.evaluate("""
            () => document.querySelectorAll('#components-tbody tr').length
        """)
        
        print(f"Initial table has {initial_rows} rows")
        
        # Test filtering by MIT
        await page.select_option("#license-filter", "MIT")
        
        # Wait a moment for filtering to take effect
        await page.wait_for_timeout(500)
        
        # Check which rows are visible after filtering
        visible_rows = await page.evaluate("""
            () => {
                const rows = document.querySelectorAll('#components-tbody tr');
                return Array.from(rows).map(row => ({
                    license: row.getAttribute('data-license') || '',
                    visible: window.getComputedStyle(row).display !== 'none' && row.style.display !== 'none',
                    style_display: row.style.display,
                    computed_display: window.getComputedStyle(row).display
                }));
            }
        """)
        
        print(f"Rows after MIT filtering: {visible_rows}")
        
        # Count visible rows
        visible_count = sum(1 for row in visible_rows if row['visible'])
        print(f"Visible rows after MIT filter: {visible_count}")
        
        # Should show MIT rows (component-mit and component-pypi-enhanced)
        mit_rows = [row for row in visible_rows if 'MIT' in row['license']]
        non_mit_rows = [row for row in visible_rows if row['license'] and 'MIT' not in row['license']]
        
        print(f"MIT rows: {mit_rows}")
        print(f"Non-MIT rows: {non_mit_rows}")
        
        # Test that MIT rows are visible
        for row in mit_rows:
            assert row['visible'], f"MIT row should be visible: {row}"
        
        # Test that non-MIT rows are hidden
        for row in non_mit_rows:
            assert not row['visible'], f"Non-MIT row should be hidden: {row}"
        
        # Test switching to "All Licenses" shows all rows again
        await page.select_option("#license-filter", "")
        await page.wait_for_timeout(500)
        
        all_visible_rows = await page.evaluate("""
            () => {
                const rows = document.querySelectorAll('#components-tbody tr');
                return Array.from(rows).filter(row => 
                    window.getComputedStyle(row).display !== 'none' && row.style.display !== 'none'
                ).length;
            }
        """)
        
        print(f"Visible rows after 'All Licenses': {all_visible_rows}")
        assert all_visible_rows == initial_rows, f"All rows should be visible again. Expected {initial_rows}, got {all_visible_rows}"
        
        # Test filtering by Apache-2.0
        await page.select_option("#license-filter", "Apache-2.0")
        await page.wait_for_timeout(500)
        
        apache_visible_rows = await page.evaluate("""
            () => {
                const rows = document.querySelectorAll('#components-tbody tr');
                const visible = Array.from(rows).filter(row => 
                    window.getComputedStyle(row).display !== 'none' && row.style.display !== 'none'
                );
                return visible.map(row => row.getAttribute('data-license') || '');
            }
        """)
        
        print(f"Visible licenses after Apache filter: {apache_visible_rows}")
        
        # Should only show Apache-2.0 rows
        for license_name in apache_visible_rows:
            assert 'Apache-2.0' in license_name, f"Only Apache rows should be visible, but found: {license_name}"
        
    finally:
        # Clean up the test file
        if sbom_file.exists():
            sbom_file.unlink()


@pytest.mark.asyncio
async def test_license_filter_debugging(page: Any) -> None:
    """Debug test to understand what's happening with the license filter."""
    
    await page.goto("http://localhost:8000/public/index.html")
    await page.wait_for_load_state("networkidle")
    
    # Check if the filter exists but is hidden
    filter_info = await page.evaluate("""
        () => {
            const filter = document.getElementById('license-filter');
            const section = document.getElementById('components-section');
            
            return {
                filter_exists: !!filter,
                filter_visible: filter ? window.getComputedStyle(filter).display !== 'none' : false,
                filter_style_display: filter ? filter.style.display : 'no filter',
                section_exists: !!section,
                section_visible: section ? window.getComputedStyle(section).display !== 'none' : false,
                section_style_display: section ? section.style.display : 'no section',
                load_btn_exists: !!document.getElementById('load-sbom-btn')
            };
        }
    """)
    
    print(f"Debug info: {filter_info}")
    
    # Check if setupTableControls was called
    setup_info = await page.evaluate("""
        () => {
            // Check if the function exists
            const hasSetupFunction = typeof setupTableControls === 'function';
            
            // Check if event listeners are attached
            const filter = document.getElementById('license-filter');
            let hasEventListeners = false;
            
            if (filter) {
                // Try to detect event listeners (this might not work in all browsers)
                const listeners = window.getEventListeners ? window.getEventListeners(filter) : {};
                hasEventListeners = Object.keys(listeners).length > 0;
            }
            
            return {
                setupTableControls_exists: hasSetupFunction,
                filter_has_listeners: hasEventListeners,
                populateLicenseFilter_exists: typeof populateLicenseFilter === 'function'
            };
        }
    """)
    
    print(f"Setup info: {setup_info}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
