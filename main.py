import streamlit as st
from app.llm import GenerateQuery
from app.query import ExecuteQuery

def main():
    st.set_page_config(
        page_title="Natural Language To Database Query",
        layout="wide"
    )
    
    st.title("Natural Language To Database Query")
    st.write("Convert natural language questions about Ethereum blockchain data into SQL queries")
    
    query = st.text_input("Enter your natural language query:", 
                         placeholder="e.g. 'Show last 5 transactions")
    
    if st.button("Submit Query"):
        if not query.strip():
            st.error("Please enter a valid query")
            return
            
        with st.spinner("Generating SQL query..."):
            try:
                generated = GenerateQuery.generate_query(query)
                print("Generated Query:", generated)
                st.write("Raw generated output:", generated)
                
                st.subheader("Generated SQL Query")
                st.code(generated['query'], language='sql')
                
                st.subheader("Query Explanation")
                st.write(generated['explanation'])
                
                with st.spinner("Executing query..."):
                    columns, data = ExecuteQuery.execute_query(generated['query'])
                    
                    st.subheader(f"Results ({len(data)} rows found)")
                    if data:
                        st.dataframe(
                            data=data,
                            column_config={col: col.capitalize() for col in columns},
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No results found")
                        
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")

if __name__ == "__main__":
    main()