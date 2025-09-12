import { useState, useRef, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';

interface Message {
  text: string;
  isUser: boolean;
  isProgress?: boolean;
}

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const formatMarkdown = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  };

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    // Add user message
    setMessages(prev => [...prev, { text: inputValue, isUser: true }]);
    setInputValue('');

    try {
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: inputValue }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (reader) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.event === 'progress') {
                setMessages(prev => [...prev, { text: data.data, isUser: false, isProgress: true }]);
              } else if (data.event === 'complete') {
                console.log('Processing complete');
              } else if (data.event === 'error') {
                toast({
                  variant: "destructive",
                  title: "Error",
                  description: data.data,
                });
              } else if (data.status === 'success') {
                const report = `🏥 **PRISM-AD Alzheimer's Risk Assessment**

**Risk Level:** ${data.risk_level}
**FDA Stage:** ${data.fda_stage}

**Executive Summary:**
${data.executive_summary}

**Key Findings:**
${data.key_findings.slice(0, 3).map((finding: string) => '• ' + finding).join('\n')}

**Clinical Recommendations:**
${data.clinical_recommendations.slice(0, 3).map((rec: string) => '• ' + rec).join('\n')}

**Follow-up:** ${data.follow_up_timeline}
**Confidence:** ${data.confidence_score || 'N/A'}

---
*This assessment was generated using the PRISM-AD multi-agent system for Alzheimer's disease risk evaluation.*`;
                setMessages(prev => [...prev.filter(m => !m.isProgress), { text: report, isUser: false }]);
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      toast({
        variant: "destructive",
        title: "Connection Error",
        description: "Could not connect to the server",
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="container mx-auto max-w-4xl p-4">
      <Card className="p-6">
        <h1 className="mb-2 text-3xl font-bold">PRISM-AD Clinical Assessment System</h1>
        <p className="mb-6 text-muted-foreground">
          <strong>Clinical AI System for Alzheimer's Disease Risk Assessment</strong><br />
          Enter clinical information, lab results, or patient descriptions for comprehensive analysis.
        </p>

        <ScrollArea className="mb-6 h-[400px] rounded-md border p-4" ref={scrollAreaRef}>
          {messages.map((message, index) => (
            message.isProgress ? (
              <Alert key={index} className="mb-2 bg-orange-50">
                <AlertDescription>{message.text}</AlertDescription>
              </Alert>
            ) : (
              <div
                key={index}
                className={`mb-4 rounded-lg p-3 ${
                  message.isUser
                    ? 'ml-12 bg-blue-50'
                    : 'mr-12 bg-gray-50 font-mono text-sm'
                }`}
                dangerouslySetInnerHTML={{ __html: formatMarkdown(message.text) }}
              />
            )
          ))}
        </ScrollArea>

        <div className="flex gap-4">
          <Textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter clinical information (e.g., '75-year-old male with MMSE 23, ApoE4 positive, CSF Aβ42 480 pg/mL...')"
            className="min-h-[80px]"
          />
          <Button onClick={sendMessage} className="shrink-0">
            Send
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default Index;
