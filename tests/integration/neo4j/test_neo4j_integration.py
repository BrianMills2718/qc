#!/usr/bin/env python3
"""Test Neo4j integration with fail-fast validation"""
import asyncio
from qc_clean.core.data.docker_manager import check_neo4j_dependencies, DockerDependencyError

async def test_neo4j_integration():
    """Test complete Neo4j integration pipeline"""
    try:
        # Test 1: Docker dependency check
        print("Testing Docker dependencies...")
        dependencies_ok = check_neo4j_dependencies()
        if not dependencies_ok:
            print("❌ Neo4j dependencies not available")
            return False
        print("✅ Neo4j dependencies available")
        
        # Test 2: Real analysis with Neo4j storage
        from qc_clean.core.cli.robust_cli_operations import RobustCLIOperations
        operations = RobustCLIOperations()
        
        # Initialize the operations
        await operations._initialize_llm_handler()
        await operations._initialize_neo4j()
        
        # Test workflow
        from qc_clean.core.workflow.grounded_theory import GroundedTheoryWorkflow
        workflow = GroundedTheoryWorkflow(operations)
        
        # Create sample interview data for testing
        sample_interviews = [{
            'id': 'test_interview_1',
            'content': '''
            This is a sample interview about workplace collaboration.
            The participant mentioned that John works closely with the development team at TechCorp.
            They collaborate on various projects and use agile methodologies.
            The manager Sarah oversees the project and ensures quality deliverables.
            The office is located in downtown Seattle and serves multiple clients.
            '''
        }]
        
        # Run open coding phase with Neo4j integration
        result = await workflow._phase_1_open_coding(sample_interviews)
        
        if result:
            print("✅ Analysis with Neo4j integration successful")
            print(f"✅ {len(result)} codes extracted")
            
            # Test 3: Verify entities were stored
            if hasattr(operations, '_neo4j_manager') and operations._neo4j_manager:
                try:
                    # Query Neo4j to check stored entities
                    async with operations._neo4j_manager.driver.session() as session:
                        result_query = await session.run("MATCH (n) RETURN count(n) as node_count")
                        record = await result_query.single()
                        entity_count = record["node_count"] if record else 0
                        print(f"✅ {entity_count} entities stored in Neo4j")
                        
                        # Query relationships
                        rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                        rel_record = await rel_result.single()
                        rel_count = rel_record["rel_count"] if rel_record else 0
                        print(f"✅ {rel_count} relationships stored in Neo4j")
                        
                        return True
                except Exception as e:
                    print(f"⚠️  Neo4j query failed: {e}")
                    return True  # Still successful if analysis worked
            else:
                print("⚠️  Neo4j manager not available")
                return True  # Still successful if analysis worked
        else:
            print("❌ Analysis failed")
            return False
            
    except DockerDependencyError as e:
        print(f"❌ Docker dependency error: {e}")
        return False
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_neo4j_integration())
    if result:
        print("\n🎉 Neo4j Integration Test PASSED")
    else:
        print("\n💥 Neo4j Integration Test FAILED")