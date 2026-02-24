import { Typography, Card, Row, Col, Tag, Steps } from 'antd';
import {
  FundOutlined,
  RocketOutlined,
  ExperimentOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph, Text } = Typography;

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  path?: string;
  comingSoon?: boolean;
  color: string;
}

const FeatureCard: React.FC<FeatureCardProps> = ({
  icon,
  title,
  description,
  path,
  comingSoon,
  color,
}) => {
  const navigate = useNavigate();

  const handleClick = () => {
    if (path && !comingSoon) {
      navigate(path);
    }
  };

  return (
    <Card
      hoverable={!comingSoon}
      onClick={handleClick}
      style={{
        cursor: comingSoon ? 'not-allowed' : 'pointer',
        opacity: comingSoon ? 0.6 : 1,
        position: 'relative',
      }}
    >
      {comingSoon && (
        <Tag color="orange" style={{ position: 'absolute', top: 8, right: 8 }}>
          即将上线
        </Tag>
      )}
      <div style={{ fontSize: 32, color, marginBottom: 12 }}>{icon}</div>
      <Title level={4} style={{ marginBottom: 8 }}>
        {title}
      </Title>
      <Paragraph style={{ marginBottom: 0, color: '#666' }}>{description}</Paragraph>
    </Card>
  );
};

const Home: React.FC = () => {
  const navigate = useNavigate();

  const features: FeatureCardProps[] = [
    {
      icon: <ExperimentOutlined />,
      title: '因子管理',
      description: '创建和管理量化因子，分析因子有效性。',
      path: '/factors',
      color: '#1890ff',
    },
    {
      icon: <ThunderboltOutlined />,
      title: '策略管理',
      description: '编写交易策略，运行回测验证策略效果。',
      path: '/strategies',
      color: '#52c41a',
    },
    {
      icon: <FundOutlined />,
      title: '沙盒模拟',
      description: '虚拟账户模拟交易，验证策略实盘效果。',
      path: '/sandbox',
      color: '#722ed1',
    },
    {
      icon: <DatabaseOutlined />,
      title: '数据中心',
      description: '查看股票行情、管理股票池。',
      path: '/stocks',
      color: '#13c2c2',
    },
    {
      icon: <RocketOutlined />,
      title: '自动交易',
      description: '策略自动执行，7x24小时不间断运行。',
      comingSoon: true,
      color: '#eb2f96',
    },
  ];

  const quickStartSteps = [
    {
      title: '创建股票池',
      description: '选择要交易的股票范围',
      onClick: () => navigate('/stocks'),
    },
    {
      title: '选择策略',
      description: '使用内置策略或自定义',
      onClick: () => navigate('/strategies'),
    },
    {
      title: '运行回测',
      description: '验证策略历史表现',
      onClick: () => navigate('/strategies'),
    },
    {
      title: '沙盒模拟',
      description: '虚拟账户实盘验证',
      onClick: () => navigate('/sandbox'),
    },
  ];

  return (
    <div>
      <Title level={2}>欢迎使用 EasyQuant</Title>
      <Paragraph style={{ fontSize: 16, color: '#666' }}>
        一站式量化交易平台，助您轻松实现投资策略自动化。
      </Paragraph>

      <Card style={{ marginTop: 24, marginBottom: 24 }}>
        <Title level={4} style={{ marginBottom: 16 }}>
          🚀 快速开始
        </Title>
        <Steps
          items={quickStartSteps.map((step) => ({
            title: (
              <Text
                style={{ cursor: 'pointer' }}
                onClick={step.onClick}
              >
                {step.title}
              </Text>
            ),
            description: step.description,
          }))}
        />
      </Card>

      <Title level={4} style={{ marginBottom: 16 }}>
        功能模块
      </Title>
      <Row gutter={[16, 16]}>
        {features.map((feature, index) => (
          <Col xs={24} sm={12} lg={8} key={index}>
            <FeatureCard {...feature} />
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default Home;
