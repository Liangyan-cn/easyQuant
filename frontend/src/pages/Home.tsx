import { Typography, Card, Row, Col, Tag } from 'antd';
import {
  LineChartOutlined,
  FundOutlined,
  RocketOutlined,
  ExperimentOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph } = Typography;

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
      description: '编写交易策略，使用内置策略或自定义策略。',
      path: '/strategies',
      color: '#52c41a',
    },
    {
      icon: <LineChartOutlined />,
      title: '策略回测',
      description: '基于历史数据验证您的交易策略，优化参数配置。',
      path: '/strategies',
      color: '#faad14',
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

  return (
    <div>
      <Title level={2}>欢迎使用 EasyQuant</Title>
      <Paragraph style={{ fontSize: 16, color: '#666' }}>
        一站式量化交易平台，助您轻松实现投资策略自动化。
      </Paragraph>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
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
