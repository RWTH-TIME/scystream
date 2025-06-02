import { useSelectedProject } from "@/hooks/useSelectedProject"
import { useGetComputeBlocksConfigurationByProjectQuery } from "@/mutations/computeBlockMutation"


export default function ProjectDetail() {
  const { selectedProject, setSelectedProject } = useSelectedProject()

  const { data, isLoading, isError } = useGetComputeBlocksConfigurationByProjectQuery(selectedProject?.uuid)

  return (
    <div>
      test
    </div>
  )
}
