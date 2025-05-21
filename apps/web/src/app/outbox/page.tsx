'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';

interface Message {
  id: string;
  type: string;
  timestamp: string;
  sender: string;
  recipient: string;
  content: any;
}

interface AgentOutbox {
  agent: string;
  messages: Message[];
}

const fetchOutboxData = async (): Promise<AgentOutbox[]> => {
  // In production, this would make an actual API call
  // For now, we'll fetch directly from the file system using a simulated API call
  
  // Simulate API response with sample data
  const agents = ['ARCH', 'CA', 'CC', 'WA'];
  const response = await Promise.all(
    agents.map(async (agent) => {
      try {
        const res = await fetch(`/api/outbox/${agent}`);
        if (!res.ok) throw new Error(`Failed to fetch ${agent} outbox`);
        const messages = await res.json();
        return { agent, messages };
      } catch (error) {
        console.error(`Error fetching ${agent} outbox:`, error);
        return { agent, messages: [] };
      }
    })
  );
  
  return response;
};

const OutboxVisualizerPage = () => {
  const [outboxData, setOutboxData] = useState<AgentOutbox[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchOutboxData();
        setOutboxData(data);
        setLoading(false);
      } catch (error) {
        console.error('Error loading outbox data:', error);
        toast({
          title: 'Error',
          description: 'Failed to load outbox data. Please try again.',
          variant: 'destructive',
        });
        setLoading(false);
      }
    };

    loadData();
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      loadData();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [toast]);

  const getMessageTypeColor = (type: string) => {
    switch (type) {
      case 'task_assignment':
        return 'bg-blue-500';
      case 'task_status':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };
  
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">Outbox Visualizer</h1>
      
      <Tabs defaultValue="all">
        <TabsList className="mb-4">
          <TabsTrigger value="all">All Agents</TabsTrigger>
          {outboxData.map((agentData) => (
            <TabsTrigger key={agentData.agent} value={agentData.agent}>
              {agentData.agent}
            </TabsTrigger>
          ))}
        </TabsList>
        
        <TabsContent value="all">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {outboxData.map((agentData) => (
              <Card key={agentData.agent} className="overflow-hidden">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{agentData.agent} Outbox</span>
                    <Badge>{agentData.messages.length} Messages</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[300px]">
                    <Accordion type="single" collapsible className="w-full">
                      {agentData.messages.length > 0 ? (
                        agentData.messages.map((message) => (
                          <AccordionItem key={message.id} value={message.id}>
                            <AccordionTrigger className="text-left">
                              <div className="flex flex-col sm:flex-row sm:items-center gap-2 w-full">
                                <Badge className={getMessageTypeColor(message.type)}>
                                  {message.type}
                                </Badge>
                                <span className="text-sm">To: {message.recipient}</span>
                                <span className="text-xs text-gray-500 ml-auto">
                                  {formatTimestamp(message.timestamp)}
                                </span>
                              </div>
                            </AccordionTrigger>
                            <AccordionContent>
                              <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-md overflow-auto">
                                <pre className="text-xs">
                                  {JSON.stringify(message.content, null, 2)}
                                </pre>
                              </div>
                            </AccordionContent>
                          </AccordionItem>
                        ))
                      ) : (
                        <p className="text-gray-500 italic p-2">No messages</p>
                      )}
                    </Accordion>
                  </ScrollArea>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
        
        {outboxData.map((agentData) => (
          <TabsContent key={agentData.agent} value={agentData.agent}>
            <Card>
              <CardHeader>
                <CardTitle>
                  {agentData.agent} Outbox
                  <Badge className="ml-2">{agentData.messages.length} Messages</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[500px]">
                  <Accordion type="single" collapsible className="w-full">
                    {agentData.messages.length > 0 ? (
                      agentData.messages.map((message) => (
                        <AccordionItem key={message.id} value={message.id}>
                          <AccordionTrigger className="text-left">
                            <div className="flex flex-col sm:flex-row sm:items-center gap-2 w-full">
                              <Badge className={getMessageTypeColor(message.type)}>
                                {message.type}
                              </Badge>
                              <span className="font-medium">{message.id}</span>
                              <span className="text-sm">→ {message.recipient}</span>
                              <span className="text-xs text-gray-500 ml-auto">
                                {formatTimestamp(message.timestamp)}
                              </span>
                            </div>
                          </AccordionTrigger>
                          <AccordionContent>
                            <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-md overflow-auto">
                              <pre className="text-xs">
                                {JSON.stringify(message, null, 2)}
                              </pre>
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      ))
                    ) : (
                      <p className="text-gray-500 italic p-2">No messages</p>
                    )}
                  </Accordion>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
};

export default OutboxVisualizerPage;