import streamlit as st
import pandas as pd
from core.data.model import RelationshipCanvas, OperationType

def sanitize_table_name(file_name, sheet_name=None):
    """Clean table names from file/sheet names"""
    import os
    base = os.path.splitext(file_name)[0]
    if sheet_name:
        clean_sheet = "".join(c if c.isalnum() else "_" for c in sheet_name)
        if clean_sheet != base and clean_sheet not in ["Sheet1", "Sheet"]:
            return f"{base}_{clean_sheet}"
    return base

def _load_uploaded_csv_file(file) -> tuple:
    """Enhanced CSV loader with encoding/separator options"""
    try:
        # Create columns for configuration
        col1, col2 = st.columns(2)
        
        with col1:
            encoding = st.selectbox(
                f"Encoding for {file.name}",
                ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1'],
                index=0,
                key=f"csv_enc_{file.file_id}"
            )
        
        with col2:
            separator = st.selectbox(
                f"Separator for {file.name}",
                [',', ';', '\t', '|'],
                index=0,
                key=f"csv_sep_{file.file_id}"
            )
        
        # Reset file pointer and load
        file.seek(0)
        df = pd.read_csv(file, encoding=encoding, sep=separator, encoding_errors='replace')
        
        if df.empty:
            return None, sanitize_table_name(file.name), "CSV file is empty"
            
        return df, sanitize_table_name(file.name), None
        
    except Exception as e:
        return None, sanitize_table_name(file.name), str(e)

def _load_uploaded_excel_file(file) -> tuple:
    """Enhanced Excel loader with multi-sheet support and proper file pointer handling"""
    try:
        # Read the Excel file once
        file.seek(0)
        xls = pd.ExcelFile(file, engine='openpyxl')
        
        if len(xls.sheet_names) == 0:
            return None, sanitize_table_name(file.name), "Excel file has no sheets"
        
        # Let user choose sheet for multi-sheet files
        if len(xls.sheet_names) > 1:
            selected_sheet = st.selectbox(
                f"Select sheet from {file.name}",
                xls.sheet_names,
                key=f"excel_sheet_{file.file_id}"
            )
        else:
            selected_sheet = xls.sheet_names[0]
        
        # CRITICAL FIX: Reset file pointer before reading the selected sheet
        file.seek(0)
        df = pd.read_excel(file, sheet_name=selected_sheet, engine='openpyxl')
        
        if df.empty:
            return None, sanitize_table_name(file.name, selected_sheet), f"Sheet '{selected_sheet}' is empty"
            
        table_name = sanitize_table_name(file.name, selected_sheet)
        return df, table_name, None
        
    except Exception as e:
        return None, sanitize_table_name(file.name), str(e)

def _get_unique_table_name(base_name: str) -> str:
    """Generate unique table name avoiding conflicts"""
    existing_names = list(st.session_state.relationship_datasets.keys())
    
    if base_name not in existing_names:
        return base_name
    
    counter = 1
    while f"{base_name}_{counter}" in existing_names:
        counter += 1
    
    new_name = f"{base_name}_{counter}"
    st.warning(f"Renamed duplicate table: {base_name} → {new_name}")
    return new_name

def handle_modeling_uploads():
    """Handle multi-file uploads with proper file pointer management"""
    st.subheader("📤 Add More Tables")
    
    # Cap at 10 tables to prevent memory issues
    current_count = len([k for k, v in st.session_state.relationship_datasets.items() if v is not None])
    if current_count >= 10:
        st.warning("⚠️ Maximum 10 tables allowed. Remove some tables to add more.")
        return
    
    uploaded_files = st.file_uploader(
        "Upload CSV or Excel files",
        type=['csv', 'xlsx', 'xls'],
        accept_multiple_files=True,
        help=f"Each file becomes a table you can join ({current_count}/10 used)",
        key="modeling_uploader"
    )
    
    if not uploaded_files:
        return
    
    for file in uploaded_files:
        # Check limit again in case of multiple files
        if len([k for k, v in st.session_state.relationship_datasets.items() if v is not None]) >= 10:
            st.warning("Reached 10 table limit. Some files were not processed.")
            break
            
        with st.spinner(f"Loading {file.name}..."):
            try:
                if file.name.endswith('.csv'):
                    # Enhanced CSV loading with encoding/separator options
                    df, table_name, error = _load_uploaded_csv_file(file)
                    if error:
                        st.error(f"❌ Failed to load {file.name}: {error}")
                        continue
                    
                    # Handle duplicate names
                    final_name = _get_unique_table_name(table_name)
                    st.session_state.relationship_datasets[final_name] = df
                    st.success(f"✅ Added '{final_name}' ({df.shape[0]:,} rows, {df.shape[1]} columns)")
                    
                else:  # Excel - MULTI-SHEET SUPPORT WITH FIXED FILE POINTER
                    df, table_name, error = _load_uploaded_excel_file(file)
                    if error:
                        st.error(f"❌ Failed to load {file.name}: {error}")
                        continue
                    
                    if df is not None:
                        final_name = _get_unique_table_name(table_name)
                        st.session_state.relationship_datasets[final_name] = df
                        st.success(f"✅ Added '{final_name}' ({df.shape[0]:,} rows, {df.shape[1]} columns)")
                    else:
                        st.error(f"❌ No valid data loaded from {file.name}")
                
            except Exception as e:
                st.error(f"❌ Error processing {file.name}: {str(e)}")

def promote_join_result(df_joined):
    """Promote join result to main dataset with smart filter preservation AND tab switch"""
    # Snapshot current filters
    old_filters = st.session_state.filters.copy()
    old_null_handling = st.session_state.null_handling.copy()
    
    # Update main dataset
    st.session_state.dataset = df_joined
    st.session_state.original_dataset = df_joined.copy()
    st.session_state.base_dataset = df_joined.copy()
    
    # Preserve only filters for columns that still exist
    new_cols = set(df_joined.columns)
    preserved_filters = {
        col: config for col, config in old_filters.items() 
        if col in new_cols
    }
    preserved_null_handling = {
        col: method for col, method in old_null_handling.items()
        if col in new_cols
    }
    
    st.session_state.filters = preserved_filters
    st.session_state.null_handling = preserved_null_handling
    
    # Update applied state to match
    st.session_state.applied_state = {
        'filters': preserved_filters.copy(),
        'null_handling': preserved_null_handling.copy(),
        'logic_mode': st.session_state.logic_mode,
        'logic_groups': st.session_state.logic_groups.copy()
    }
    
    # Clear analysis state
    from app import SessionStateManager
    SessionStateManager.reset_analysis()
    
    # CRITICAL FIX: Switch to Overview tab
    st.session_state.active_tab = "Dataset Overview"
    
    # Success message will show in Overview tab
    preserved_count = len(preserved_filters)
    total_count = len(old_filters)
    st.session_state.promote_success_message = f"✅ Joined dataset promoted! {preserved_count}/{total_count} filters preserved"

def render_table_management_section():
    """Render the table management section with enhanced UI"""
    # Check if we have enough tables
    datasets = {k: v for k, v in st.session_state.relationship_datasets.items() if v is not None}
    valid_tables = list(datasets.keys())
    
    # Enhanced file upload section with better UI
    with st.container(border=True):
        st.subheader("📁 Data Sources")
        
        col_info, col_sync = st.columns([3, 1])
        with col_info:
            st.caption("Upload additional datasets to build relationships. Your current dataset is available as 'main'.")
        with col_sync:
            if st.button("🔄 Sync Main", help="Update main table with current dataset", key="btn_sync_main", use_container_width=True):
                st.session_state.relationship_datasets['main'] = st.session_state.dataset.copy()
                # Clear stale results when structure changes
                st.session_state.join_result = None
                st.success("Main table synced!")
                st.rerun()
        
        # File upload with better UI
        uploaded_files = st.file_uploader(
            "Select CSV or Excel files",
            type=['csv', 'xlsx', 'xls'],
            accept_multiple_files=True,
            help="Each file becomes a table. Excel files with multiple sheets will prompt for sheet selection.",
            key="enhanced_modeling_uploader",
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            if st.button("📥 Load Selected Files", type="primary", use_container_width=True, key="btn_load_uploads"):
                new_tables = 0
                for file in uploaded_files:
                    # Size guard (150MB limit)
                    if file.size > 150 * 1024 * 1024:
                        st.error(f"❌ {file.name} > 150 MB – skipped.")
                        continue
                    
                    try:
                        if file.name.endswith('.csv'):
                            df, table_name, error = _load_uploaded_csv_file(file)
                        else:
                            df, table_name, error = _load_uploaded_excel_file(file)
                        
                        if df is not None and not df.empty:
                            final_name = _get_unique_table_name(table_name)
                            st.session_state.relationship_datasets[final_name] = df
                            new_tables += 1
                            st.success(f"✅ Loaded {final_name} ({len(df):,} rows)")
                        elif error:
                            st.error(f"❌ {file.name}: {error}")
                            
                    except Exception as e:
                        st.error(f"❌ Error loading {file.name}: {str(e)}")
                
                if new_tables > 0:
                    # Clear stale results when new tables are added
                    st.session_state.join_result = None
                    st.session_state.relationship_links = []
                    st.rerun()
    
    # Current Tables Display
    if valid_tables:
        st.subheader("📚 Current Tables")
        
        # Table metrics
        total_rows = sum(len(df) for df in datasets.values())
        total_cols = sum(len(df.columns) for df in datasets.values())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tables", len(valid_tables))
        with col2:
            st.metric("Total Rows", f"{total_rows:,}")
        with col3:
            st.metric("Total Columns", total_cols)
        
        # Table cards in columns
        cols = st.columns(2)
        for i, table_name in enumerate(valid_tables):
            with cols[i % 2]:
                df = datasets[table_name]
                with st.container(border=True):
                    # Header with status
                    col_header, col_actions = st.columns([3, 1])
                    with col_header:
                        if table_name == 'main':
                            st.markdown(f"**🎯 {table_name}** (current dataset)")
                        else:
                            st.markdown(f"**📊 {table_name}**")
                    with col_actions:
                        if table_name != 'main':
                            if st.button("🗑️", key=f"remove_{table_name}", help=f"Remove {table_name}"):
                                del st.session_state.relationship_datasets[table_name]
                                # Clear links and results since structure changed
                                st.session_state.relationship_links = []
                                st.session_state.join_result = None
                                st.success(f"Removed table '{table_name}'")
                                st.rerun()
                    
                    # Table info
                    st.caption(f"📐 {df.shape[0]:,} rows × {df.shape[1]} columns")
                    
                    # Quick column preview
                    with st.expander("View columns", icon="🔍"):
                        for col in df.columns[:8]:  # First 8 columns
                            dtype = str(df[col].dtype)
                            null_count = df[col].isnull().sum()
                            null_text = f" • {null_count} nulls" if null_count > 0 else ""
                            st.write(f"• `{col}` ({dtype}){null_text}")
                        if len(df.columns) > 8:
                            st.caption(f"... and {len(df.columns) - 8} more columns")
    
    return len(valid_tables) >= 2  # Return whether we have enough tables for relationships

def render_relationship_builder_section():
    """Render the relationship builder section with enhanced UI"""
    # Get current datasets - FILTER OUT NONE VALUES
    datasets = {k: v for k, v in st.session_state.relationship_datasets.items() if v is not None}
    
    # Initialize RelationshipCanvas with ACTUAL datasets
    canvas = RelationshipCanvas(datasets)
    
    # Restore existing links to canvas
    for link in st.session_state.relationship_links:
        if len(link) == 8:  # Full join link
            from_table, from_col, to_table, to_col, op_type, alias, join_type, _ = link
            if op_type == OperationType.JOIN.value:
                canvas.add_join(from_table, from_col, to_table, to_col, join_type, alias)
    
    # Configuration Section
    with st.container(border=True):
        st.subheader("⚙️ Configuration")
        col1, col2 = st.columns(2)
        
        with col1:
            start_table = st.selectbox(
                "Start from table",
                list(datasets.keys()),
                index=0,
                help="Select which table to begin the join sequence from",
                key="relationship_start_table"
            )
        
        with col2:
            default_join_type = st.selectbox(
                "Default join type",
                ["inner", "left", "right", "outer"],
                help="Default join type when not specified",
                key="relationship_default_join_type"
            )
    
    # Add Relationship Section
    with st.container(border=True):
        st.subheader("🔗 Add Relationship")
        
        # # Relationship type selection
        # relationship_type = st.radio(
        #     "Relationship Type:",
        #     ["Join Tables", "Set Operation"],
        #     horizontal=True,
        #     key="relationship_type_selector"
        # )

        relationship_type = "Join Tables" # For now
        
        if relationship_type == "Join Tables":
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Source Table**")
                from_table = st.selectbox(
                    "Select source table", 
                    list(datasets.keys()),
                    key="join_from_table"
                )
                if from_table in datasets:
                    from_col = st.selectbox(
                        "Select column",
                        datasets[from_table].columns,
                        key="join_from_col"
                    )
            
            with col2:
                st.markdown("**Target Table**")
                to_tables = [t for t in datasets.keys() if t != from_table]
                to_table = st.selectbox(
                    "Select target table",
                    to_tables,
                    key="join_to_table"
                )
                if to_table in datasets:
                    to_col = st.selectbox(
                        "Select column", 
                        datasets[to_table].columns,
                        key="join_to_col"
                    )
            
            # Join options
            col3, col4, col5 = st.columns([1, 1, 2])
            with col3:
                join_type = st.selectbox("Join type", ["inner", "left", "right", "outer"], key="join_type_select")
            with col4:
                alias = st.text_input("Column alias", placeholder="optional", key="join_alias_input")
            with col5:
                st.write("")  # Spacer
                st.write("")  # Spacer
                if st.button("💫 Add Join", type="primary", use_container_width=True, key="btn_add_join"):
                    if from_table in datasets and to_table in datasets:
                        errors, warnings = canvas.validate_link(
                            from_table, from_col, to_table, to_col, 
                            OperationType.JOIN.value, join_type
                        )
                        
                        if errors:
                            for error in errors:
                                st.error(f"❌ {error}")
                        else:
                            for warning in warnings:
                                st.warning(f"⚠️ {warning}")
                            
                            alias_value = alias.strip() or None
                            if canvas.add_join(from_table, from_col, to_table, to_col, join_type, alias_value):
                                st.session_state.relationship_links = canvas.links
                                # Clear stale results when relationships change
                                st.session_state.join_result = None
                                st.success(f"✅ Join added: `{from_table}.{from_col}` → `{to_table}.{to_col}`")
        
        else:  # Set Operation
            st.info("Set operations combine tables with compatible structures (UNION, INTERSECT, EXCEPT)")
            col1, col2 = st.columns(2)
            
            with col1:
                table1 = st.selectbox("First table", list(datasets.keys()), key="set_table1")
            with col2:
                table2_options = [t for t in datasets.keys() if t != table1]
                table2 = st.selectbox("Second table", table2_options, key="set_table2")
            
            # Set operation options
            col3, col4, col5 = st.columns([2, 2, 1])
            with col3:
                operation = st.selectbox("Operation", ["union", "union_all", "intersect", "except"])
            with col4:
                match_by_name = st.checkbox("Match columns by name", value=True)
            with col5:
                st.write("")  # Spacer
                st.write("")  # Spacer
                if st.button("🔄 Add Set Op", type="primary", use_container_width=True, key="btn_add_setop"):
                    errors, warnings = canvas.validate_link(
                        table1, "", table2, "", OperationType.SET.value, operation, match_by_name
                    )
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        for warning in warnings:
                            st.warning(f"⚠️ {warning}")
                        
                        if canvas.add_set_operation(table1, table2, operation, None, match_by_name):
                            st.session_state.relationship_links = canvas.links
                            st.session_state.join_result = None
                            op_display = operation.upper().replace("_", " ")
                            st.success(f"✅ Set operation added: `{table1}` {op_display} `{table2}`")
    
    # Current Relationships Section
    if canvas.links:
        with st.container(border=True):
            st.subheader(f"📋 Current Relationships ({len(canvas.links)})")
            
            # Build relationships dataframe
            relationship_data = []
            for i, (from_table, from_col, to_table, to_col, op_type, alias, join_type, match_by_name) in enumerate(canvas.links):
                if op_type == OperationType.JOIN.value:
                    relationship_data.append({
                        "ID": i,
                        "Relationship": f"{from_table}.{from_col} → {to_table}.{to_col}",
                        "Type": "Join",
                        "Details": join_type or "inner",
                        "Alias": alias or "",
                        "Remove": False
                    })
            
            df_relationships = pd.DataFrame(relationship_data)
            
            # Editable dataframe
            edited_df = st.data_editor(
                df_relationships,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                    "Relationship": st.column_config.TextColumn("Relationship", disabled=True, width="medium"),
                    "Type": st.column_config.TextColumn("Type", disabled=True, width="small"),
                    "Details": st.column_config.SelectboxColumn(
                        "Join Type",
                        options=["inner", "left", "right", "outer"],
                        width="small"
                    ),
                    "Alias": st.column_config.TextColumn("Alias", width="small"),
                    "Remove": st.column_config.CheckboxColumn("Remove", width="small")
                },
                hide_index=True,
                key="relationships_editor"
            )
            
            # Handle removals and updates
            needs_rerun = False
            
            # Handle removals
            removals = []
            for i, row in edited_df.iterrows():
                if row["Remove"] and i < len(canvas.links):
                    from_table, from_col, to_table, to_col, _, _, _, _ = canvas.links[i]
                    removals.append((from_table, from_col, to_table, to_col))
            
            if removals:
                for from_table, from_col, to_table, to_col in removals:
                    canvas.remove_link(from_table, from_col, to_table, to_col)
                needs_rerun = True
            
            # Handle updates
            for i, (old_row, new_row) in enumerate(zip(df_relationships.to_dict('records'), edited_df.to_dict('records'))):
                if i < len(canvas.links):
                    old_details = old_row["Details"]
                    new_details = new_row["Details"]
                    old_alias = old_row["Alias"]
                    new_alias = new_row["Alias"]
                    
                    if old_details != new_details or old_alias != new_alias:
                        from_table, from_col, to_table, to_col, op_type, old_alias, old_join_type, match_by_name = canvas.links[i]
                        if op_type == OperationType.JOIN.value and new_details in ["inner", "left", "right", "outer"]:
                            canvas.links[i] = (
                                from_table, from_col, to_table, to_col, op_type, 
                                new_alias.strip() or None, new_details, match_by_name
                            )
                            needs_rerun = True
            
            if needs_rerun:
                st.session_state.relationship_links = canvas.links
                st.rerun()
            
            # Management buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear All Relationships", type="secondary", use_container_width=True, key="btn_clear_relationships"):
                    canvas.clear()
                    st.session_state.relationship_links = []
                    st.session_state.join_result = None
                    st.success("All relationships cleared!")
                    st.rerun()
            with col2:
                if st.button("📊 View Relationship Graph", use_container_width=True, key="btn_view_graph"):
                    st.session_state.show_relationship_graph = not st.session_state.get('show_relationship_graph', False)
                    st.rerun()
            
            # Relationship Graph
            if st.session_state.get('show_relationship_graph', False):
                try:
                    start_table = st.session_state.get("relationship_start_table", list(datasets.keys())[0])
                    dot = canvas.to_dot(start_table)
                    st.graphviz_chart(dot)
                except Exception as e:
                    st.error(f"Could not render graph: {e}")
    
    return canvas, datasets

def render_join_generation_section(canvas, datasets):
    """Render the join generation and results section"""
    if not canvas.links:
        return
    
    with st.container(border=True):
        st.subheader("🚀 Generate Joined Table")
        
        # Configuration reminder
        start_table = st.session_state.get("relationship_start_table", list(datasets.keys())[0])
        default_join_type = st.session_state.get("relationship_default_join_type", "inner")
        
        col_info, col_generate = st.columns([2, 1])
        with col_info:
            st.write(f"**Starting from:** `{start_table}`")
            st.write(f"**Default join type:** `{default_join_type}`")
        
        with col_generate:
            if st.button("✨ GENERATE JOINED TABLE", type="primary", use_container_width=True, key="btn_generate_joined"):
                # Clear any previous stale results first
                st.session_state.join_result = None
                
                is_valid, warnings = canvas.validate_graph()
                
                if not is_valid:
                    st.error("❌ Cannot generate due to issues:")
                    for warning in warnings:
                        st.error(f"• {warning}")
                else:
                    if warnings:
                        st.warning("⚠️ Considerations before generating:")
                        for warning in warnings:
                            st.warning(f"• {warning}")
                    
                    with st.spinner("🔄 Building your joined table... This may take a moment for large datasets."):
                        try:
                            # Use selected start table and default join type
                            result = canvas.join(start_table, default_join_type)
                            st.session_state.join_result = result
                            st.success(f"✅ Success! Generated table with **{result.shape[0]:,} rows** × **{result.shape[1]:,} columns**")
                            
                            # Show execution plan
                            with st.expander("📋 View Execution Plan", expanded=False):
                                for step in canvas.plan:
                                    level = step["level"]
                                    message = step["message"]
                                    if level.value == "start":
                                        st.markdown(f"**🚀 {message}**")
                                    elif level.value == "step":
                                        st.markdown(f"**▸ {message}**")
                                    elif level.value == "result":
                                        st.success(f"**✅ {message}**")
                                    elif level.value == "warn":
                                        st.warning(f"**⚠️ {message}**")
                                    elif level.value == "error":
                                        st.error(f"**❌ {message}**")
                                        
                        except Exception as e:
                            st.error(f"❌ Generation failed: {str(e)}")
    
    # Show Join Result
    if st.session_state.get('join_result') is not None:
        result = st.session_state.join_result
        
        with st.container(border=True):
            st.subheader("📊 Join Result")
            
            # Verification: Show this is actually joined data, not original
            original_cols = set()
            for df in datasets.values():
                original_cols.update(df.columns)
            
            joined_cols = set(result.columns)
            new_cols = joined_cols - original_cols
            combined_cols = joined_cols & original_cols
            
            # Results Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Rows", f"{result.shape[0]:,}")
            with col2:
                st.metric("Columns", result.shape[1])
            with col3:
                st.metric("New Columns", len(new_cols))
            with col4:
                mem_mb = result.memory_usage(deep=True).sum() / (1024 ** 2)
                st.metric("Memory", f"{mem_mb:.1f} MB")
            
            # Column Analysis
            with st.expander("🔍 Column Analysis", expanded=False):
                st.write(f"**Combined columns:** {len(combined_cols)}")
                st.write(f"**New joined columns:** {len(new_cols)}")
                if new_cols:
                    st.write("New columns:", ", ".join(sorted(new_cols)[:10]) + ("..." if len(new_cols) > 10 else ""))
            
            # Action Buttons
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                if st.button("🎯 Use This Joined Dataset", type="primary", use_container_width=True, key="btn_promote_joined"):
                    promote_join_result(result)
                    st.rerun()
            with col2:
                if st.button("📊 Preview Data", use_container_width=True, key="btn_preview_joined"):
                    st.session_state.preview_join_data = not st.session_state.get('preview_join_data', False)
                    st.rerun()
            with col3:
                # Save as table option
                new_table_name = st.text_input("Save as:", value=f"{start_table}_joined", key="new_table_name", label_visibility="collapsed")
            with col4:
                if st.button("💾 Save Table", use_container_width=True, key="btn_save_table"):
                    if new_table_name and new_table_name.strip():
                        clean_name = new_table_name.strip()
                        if clean_name not in st.session_state.relationship_datasets:
                            st.session_state.relationship_datasets[clean_name] = result.copy()
                            st.success(f"✅ Added '{clean_name}' as reusable table!")
                            st.rerun()
                        else:
                            st.error(f"❌ Table '{clean_name}' already exists")
                    else:
                        st.error("❌ Please enter a table name")
            
            # Data preview
            if st.session_state.get('preview_join_data', False):
                with st.expander("👀 Joined Data Preview (first 100 rows)", expanded=True):
                    st.dataframe(result.head(100))

# Update the render_relationships_tab function at the end of the file:

def render_relationships_tab():
    """Main function to render the relationships tab - PROFESSIONAL VERSION"""
    # CRITICAL FIX: Clear stale join result when tab is activated
    if 'last_active_tab' not in st.session_state:
        st.session_state.last_active_tab = None
    
    # FIX: Update the tab name to match where this is called from
    current_tab = "Data Preparation"
    if st.session_state.last_active_tab != current_tab:
        # We're switching to this tab - clear stale results
        st.session_state.join_result = None
        st.session_state.last_active_tab = current_tab
    
    # Initialize if needed - FIXED: Don't overwrite main table once set
    if 'relationship_datasets' not in st.session_state:
        st.session_state.relationship_datasets = {'main': st.session_state.dataset.copy()}
    
    # CRITICAL FIX: Only set main dataset if it doesn't exist or is None
    if (st.session_state.relationship_datasets.get('main') is None):
        st.session_state.relationship_datasets['main'] = st.session_state.dataset.copy()
    
    # Table Management Section
    has_enough_tables = render_table_management_section()
    
    # Early return if not enough tables
    if not has_enough_tables:
        st.info("""
        **📋 Ready to Start Modeling**  
        Upload at least one additional table above to begin building relationships.  
        Your current dataset is available as **'main'**.
        """)
        return
    
    # Relationship Builder Section
    canvas, datasets = render_relationship_builder_section()
    
    # Join Generation Section
    render_join_generation_section(canvas, datasets)