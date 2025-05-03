import streamlit as st
from app.llm import GenerateQuery
from app.query import ExecuteQuery

def main():
    st.set_page_config(
        page_title="Natural Language To Database Query",
        layout="wide"
    )
    
    st.title("Natural Language To Database Query")
    st.write("Convert natural language queries on Ethereum blockchain data into SQL queries")
    
    # Initialize session state variables if they don't exist
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    if 'page_index' not in st.session_state:
        st.session_state.page_index = 1
    if 'has_next_page' not in st.session_state:
        st.session_state.has_next_page = False
    if 'total_rows' not in st.session_state:
        st.session_state.total_rows = 0
    if 'rows_per_page' not in st.session_state:
        st.session_state.rows_per_page = 100
    if 'generated' not in st.session_state:
        st.session_state.generated = None
    if 'columns' not in st.session_state:
        st.session_state.columns = []
    if 'data' not in st.session_state:
        st.session_state.data = []
    
    query = st.text_input("Enter your natural language query:", 
                          value=st.session_state.current_query,
                          placeholder="e.g. 'Show recent transactions'")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        st.session_state.rows_per_page = st.number_input(
            "Rows per page:", 
            min_value=10, 
            max_value=500, 
            value=st.session_state.rows_per_page,
            step=10
        )
    
    if st.button("Submit Query"):
        if not query.strip():
            st.error("Please enter a valid query")
            return
        
        st.session_state.page_index = 1
        st.session_state.current_query = query
        process_query()
    
    if st.session_state.current_query:
        col1, col2, col3, col4 = st.columns([1, 1, 2, 2])
        
        with col1:
            prev_button = st.button("← Previous Page", disabled=(st.session_state.page_index <= 1))
            if prev_button and st.session_state.page_index > 1:
                st.session_state.page_index -= 1
                process_query()
                st.rerun()
        
        with col2:
            next_button = st.button("Next Page →", disabled=not st.session_state.has_next_page)
            if next_button and st.session_state.has_next_page:
                st.session_state.page_index += 1
                process_query()
                st.rerun()
        
        with col3:
            st.write(f"Page: {st.session_state.page_index}")
        
        with col4:
            if st.session_state.total_rows > 0:
                st.write(f"Total rows: {st.session_state.total_rows}")
    
    if st.session_state.generated:
        display_results()

def process_query():
    """Process the current query with the current page index"""
    query = st.session_state.current_query
    page_index = st.session_state.page_index
    rows_per_page = st.session_state.rows_per_page
    
    with st.spinner("Generating SQL query..."):
        try:
            st.session_state.generated = GenerateQuery.generate_query(
                query,
                page_index=page_index,
                rows_per_page=rows_per_page
            )
            
            if 'count_query' in st.session_state.generated:
                with st.spinner("Counting total rows..."):
                    st.session_state.total_rows = ExecuteQuery.count_rows(
                        st.session_state.generated['count_query']
                    )
                    
                st.session_state.has_next_page = (
                    page_index * rows_per_page
                ) < st.session_state.total_rows
            
            with st.spinner("Executing query..."):
                st.session_state.columns, st.session_state.data = ExecuteQuery.execute_query(
                    st.session_state.generated['query']
                )
                
                # If we don't have a count query but got exactly rows_per_page results, we might have a next page
                if 'count_query' not in st.session_state.generated and len(st.session_state.data) >= rows_per_page:
                    st.session_state.has_next_page = True
                    
                    if len(st.session_state.data) > rows_per_page:
                        st.session_state.data = st.session_state.data[:rows_per_page]
                        
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")

def display_results():
    """Display the query results and other UI elements"""
    with st.expander("Raw generated output"):
        st.write(st.session_state.generated)
    
    st.subheader("Generated SQL Query")
    st.code(st.session_state.generated['query'], language='sql')
    
    if 'explanation' in st.session_state.generated:
        st.subheader("Query Explanation")
        st.write(st.session_state.generated['explanation'])
    
    st.subheader(f"Results ({len(st.session_state.data)} rows)")
    if st.session_state.data:
        st.dataframe(
            data=st.session_state.data,
            column_config={col: col.capitalize() for col in st.session_state.columns},
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No results found")

if __name__ == "__main__":
    main()