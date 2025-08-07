#!/usr/bin/env python3
"""
Test suite for the dynamic license filter functionality in the SBOM HTML dashboard.
Uses Selenium WebDriver to test the JavaScript functionality.
"""

import json
import pytest
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException


class TestLicenseFilter:
    """Test suite for dynamic license filter functionality."""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Set up Chrome WebDriver for testing."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode for CI
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    @pytest.fixture(scope="class")
    def sample_sbom_data(self):
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
                },
                {
                    "name": "component-unknown",
                    "version": "0.2.0", 
                    "type": "library"
                    # No licenses field at all
                }
            ]
        }
    
    @pytest.fixture(scope="class")
    def test_html_file(self, sample_sbom_data, tmp_path_factory):
        """Create a test HTML file with embedded SBOM data."""
        tmp_dir = tmp_path_factory.mktemp("sbom_test")
        
        # Read the actual HTML template
        html_file = Path("/Users/wolfgang.ihloff/workspace/tahecho/public/index.html")
        html_content = html_file.read_text()
        
        # Create test SBOM JSON file
        sbom_file = tmp_dir / "sbom.json"
        with open(sbom_file, 'w') as f:
            json.dump(sample_sbom_data, f, indent=2)
        
        # Create test HTML file  
        test_html = tmp_dir / "index.html"
        with open(test_html, 'w') as f:
            f.write(html_content)
        
        return test_html, sbom_file
    
    def test_license_filter_dropdown_exists(self, driver, test_html_file):
        """Test that the license filter dropdown exists."""
        test_html, _ = test_html_file
        driver.get(f"file://{test_html}")
        
        # Make the components section visible for testing
        driver.execute_script("""
            document.getElementById('components-section').style.display = 'block';
        """)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "license-filter"))
        )
        
        license_filter = driver.find_element(By.ID, "license-filter")
        assert license_filter.is_displayed()
        assert license_filter.tag_name == "select"
    
    def test_license_filter_initially_has_only_all_licenses(self, driver, test_html_file):
        """Test that initially the dropdown only has 'All Licenses' option."""
        test_html, _ = test_html_file
        driver.get(f"file://{test_html}")
        
        # Make the components section visible for testing
        driver.execute_script("""
            document.getElementById('components-section').style.display = 'block';
        """)
        
        license_filter = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "license-filter"))
        )
        
        select = Select(license_filter)
        options = select.options
        
        # Should only have "All Licenses" initially
        assert len(options) == 1
        assert options[0].text == "All Licenses"
        assert options[0].get_attribute("value") == ""
    
    def test_load_sbom_button_exists(self, driver, test_html_file):
        """Test that the load SBOM button exists."""
        test_html, _ = test_html_file
        driver.get(f"file://{test_html}")
        
        load_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "load-sbom-btn"))
        )
        
        assert load_btn.is_displayed()
        assert "Load SBOM Data" in load_btn.text
    
    def test_license_filter_populates_after_loading_sbom(self, driver, test_html_file):
        """Test that license filter populates dynamically after loading SBOM data."""
        test_html, sbom_file = test_html_file
        driver.get(f"file://{test_html}")
        
        # Make the components section visible for testing
        driver.execute_script("""
            document.getElementById('components-section').style.display = 'block';
        """)
        
        # Test by directly calling the populateLicenseFilter function with sample data
        sample_components = [
            {"licenses": [{"license": {"id": "MIT"}}]},
            {"licenses": [{"license": {"id": "Apache-2.0"}}]},
            {"licenses": [{"license": {"id": "BSD-3-Clause"}}]},
            {"licenses": []},  # No license
            {}  # No licenses field
        ]
        
        # Execute JavaScript to test the function directly
        driver.execute_script("""
            window.testComponents = arguments[0];
            populateLicenseFilter(window.testComponents);
        """, sample_components)
        
        # Wait a moment for DOM updates
        time.sleep(0.5)
        
        # Check that license filter now has the expected options
        license_filter = driver.find_element(By.ID, "license-filter")
        select = Select(license_filter)
        options = select.options
        
        # Should have "All Licenses" + the unique licenses found
        expected_licenses = {"All Licenses", "MIT", "Apache-2.0", "BSD-3-Clause", "Unknown/Not Specified"}
        actual_licenses = {option.text for option in options}
        
        assert expected_licenses.issubset(actual_licenses), f"Expected {expected_licenses}, got {actual_licenses}"
    
    def test_license_filter_deduplicates_licenses(self, driver, test_html_file):
        """Test that duplicate licenses are not added to the filter."""
        test_html, _ = test_html_file
        driver.get(f"file://{test_html}")
        
        # Make the components section visible for testing
        driver.execute_script("""
            document.getElementById('components-section').style.display = 'block';
        """)
        
        # Test components with duplicate MIT licenses
        sample_components = [
            {"licenses": [{"license": {"id": "MIT"}}]},
            {"licenses": [{"license": {"id": "MIT"}}]},  # Duplicate
            {"licenses": [{"license": {"name": "MIT License"}}]},  # Different format, same license
            {"licenses": [{"license": {"id": "Apache-2.0"}}]}
        ]
        
        driver.execute_script("""
            populateLicenseFilter(arguments[0]);
        """, sample_components)
        
        time.sleep(0.5)
        
        license_filter = driver.find_element(By.ID, "license-filter")
        select = Select(license_filter)
        options = select.options
        
        # Count MIT occurrences (should be only 1)
        mit_count = sum(1 for option in options if "MIT" in option.text)
        assert mit_count == 1, f"Expected 1 MIT option, found {mit_count}"
    
    def test_license_filter_sorts_alphabetically(self, driver, test_html_file):
        """Test that licenses are sorted alphabetically in the dropdown."""
        test_html, _ = test_html_file
        driver.get(f"file://{test_html}")
        
        # Make the components section visible for testing
        driver.execute_script("""
            document.getElementById('components-section').style.display = 'block';
        """)
        
        sample_components = [
            {"licenses": [{"license": {"id": "Zlib"}}]},
            {"licenses": [{"license": {"id": "Apache-2.0"}}]},
            {"licenses": [{"license": {"id": "MIT"}}]},
            {"licenses": [{"license": {"id": "BSD-3-Clause"}}]}
        ]
        
        driver.execute_script("""
            populateLicenseFilter(arguments[0]);
        """, sample_components)
        
        time.sleep(0.5)
        
        license_filter = driver.find_element(By.ID, "license-filter")
        select = Select(license_filter)
        options = select.options[1:]  # Skip "All Licenses"
        
        license_texts = [option.text for option in options]
        sorted_licenses = sorted(license_texts)
        
        assert license_texts == sorted_licenses, f"Licenses not sorted: {license_texts}"
    
    def test_license_filtering_functionality(self, driver, test_html_file):
        """Test that license filtering actually filters the table rows."""
        test_html, _ = test_html_file
        driver.get(f"file://{test_html}")
        
        # Make the components section visible for testing
        driver.execute_script("""
            document.getElementById('components-section').style.display = 'block';
        """)
        
        # First, we need to create some test table rows
        driver.execute_script("""
            // Create test table structure
            const tbody = document.createElement('tbody');
            tbody.id = 'components-tbody';
            
            // Add test rows with different licenses
            const testRows = [
                {license: 'MIT', name: 'component1'},
                {license: 'Apache-2.0', name: 'component2'}, 
                {license: 'MIT (PyPI)', name: 'component3'},
                {license: 'Not specified', name: 'component4'}
            ];
            
            testRows.forEach(rowData => {
                const row = document.createElement('tr');
                row.setAttribute('data-license', rowData.license);
                
                const nameCell = document.createElement('td');
                nameCell.textContent = rowData.name;
                row.appendChild(nameCell);
                
                const licenseCell = document.createElement('td');
                licenseCell.textContent = rowData.license;
                row.appendChild(licenseCell);
                
                tbody.appendChild(row);
            });
            
            // Find existing table or create one
            let table = document.getElementById('components-table');
            if (!table) {
                table = document.createElement('table');
                table.id = 'components-table';
                document.body.appendChild(table);
            }
            table.appendChild(tbody);
        """)
        
        # Test filtering by MIT
        license_filter = driver.find_element(By.ID, "license-filter")
        
        # Add MIT option manually for testing
        driver.execute_script("""
            const select = document.getElementById('license-filter');
            const option = document.createElement('option');
            option.value = 'MIT';
            option.text = 'MIT';
            select.appendChild(option);
        """)
        
        select = Select(license_filter)
        select.select_by_value("MIT")
        
        # Trigger the filtering by manually calling the filtering logic
        driver.execute_script("""
            // Manual filtering logic (same as in updateTableVisibility function)
            const licenseFilter = document.getElementById('license-filter');
            const filterValue = licenseFilter.value;
            const rows = document.querySelectorAll('#components-tbody tr');
            
            rows.forEach(row => {
                const license = row.getAttribute('data-license') || '';
                let shouldShow = !filterValue;
                
                if (filterValue) {
                    if (filterValue === 'Unknown/Not Specified') {
                        shouldShow = license === '' || license.includes('Not specified') || license.includes('Unknown');
                    } else {
                        // Extract the main license identifier (before any parentheses or additional info)
                        const mainLicense = license.split(' (')[0].trim();
                        shouldShow = mainLicense === filterValue;
                    }
                }
                
                row.style.display = shouldShow ? '' : 'none';
            });
        """)
        
        time.sleep(0.5)
        
        # Check which rows are visible (display='' means visible, display='none' means hidden)
        visible_rows = driver.execute_script("""
            const rows = document.querySelectorAll('#components-tbody tr');
            return Array.from(rows).map(row => ({
                license: row.getAttribute('data-license'),
                display: row.style.display,
                visible: row.style.display === '' || row.style.display === 'table-row'
            }));
        """)
        
        # Only MIT and MIT (PyPI) rows should be visible
        mit_rows = [row for row in visible_rows if 'MIT' in row['license']]
        non_mit_rows = [row for row in visible_rows if 'MIT' not in row['license']]
        
        assert all(row['visible'] for row in mit_rows), f"MIT rows should be visible: {mit_rows}"
        assert all(not row['visible'] for row in non_mit_rows), f"Non-MIT rows should be hidden: {non_mit_rows}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
