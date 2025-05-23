export async function parseYamlFile(file: File): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        // In a real implementation, we would parse the YAML here
        // For now, we'll just resolve with a mock plan
        const mockPlan = {
          id: `uploaded-${Date.now()}`,
          name: file.name,
          description: 'Uploaded plan',
          tasks: [
            {
              id: 'task-1',
              name: 'Sample Task',
              agent: 'sample-agent',
              status: 'pending'
            }
          ]
        };
        resolve(mockPlan);
      } catch (error) {
        reject(new Error('Failed to parse YAML file'));
      }
    };
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    reader.readAsText(file);
  });
}
